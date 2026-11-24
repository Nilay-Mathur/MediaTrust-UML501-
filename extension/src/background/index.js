// MediaTrust Background Service Worker (Manifest V3)

const DEFAULT_SETTINGS = {
  backendUrl: 'http://127.0.0.1:8000/api/v1',
  autoPageMonitor: true,
    autoVideoMonitor: true,
  hideLowRisk: true,
  debounceMs: 1200,
  enabledSites: ['instagram.com', 'youtube.com', 'tiktok.com', 'facebook.com', 'x.com', 'localhost'],
};

// Initialize settings on install
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get(['settings'], (res) => {
    if (!res.settings) {
      chrome.storage.local.set({ settings: DEFAULT_SETTINGS });
    }
  });

  // Create context menus
  chrome.contextMenus.create({
    id: 'mediatrust-text',
    title: 'MediaTrust: Check text for scam/phishing',
    contexts: ['selection'],
  });

  chrome.contextMenus.create({
    id: 'mediatrust-link',
    title: 'MediaTrust: Inspect link for threats',
    contexts: ['link'],
  });

  chrome.contextMenus.create({
    id: 'mediatrust-image',
    title: 'MediaTrust: Analyze image authenticity',
    contexts: ['image'],
  });
});

// Context Menu Action Handler
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  const { settings } = await chrome.storage.local.get(['settings']);
  const backendUrl = settings?.backendUrl || DEFAULT_SETTINGS.backendUrl;

  if (info.menuItemId === 'mediatrust-text' && info.selectionText) {
    try {
      const res = await fetch(`${backendUrl}/analyze/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: info.selectionText.substring(0, 5000) }),
      });
      const data = await res.json();
      if (tab?.id) {
        chrome.tabs.sendMessage(tab.id, {
          type: 'DISPLAY_NOTIFICATION',
          payload: data,
        });
      }
    } catch (err) {
      console.error('MediaTrust context menu text error:', err);
    }
  } else if (info.menuItemId === 'mediatrust-link' && info.linkUrl) {
    try {
      const res = await fetch(`${backendUrl}/analyze/url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: info.linkUrl }),
      });
      const data = await res.json();
      if (tab?.id) {
        chrome.tabs.sendMessage(tab.id, {
          type: 'DISPLAY_NOTIFICATION',
          payload: data,
        });
      }
    } catch (err) {
      console.error('MediaTrust context menu link error:', err);
    }
  }
});

async function captureVideoCrop(windowId, targetTabId, crop, maxDimension = 384) {
  if (!Number.isInteger(windowId) || !crop) return null;
  const [activeTab] = await chrome.tabs.query({ active: true, windowId });
  if (!activeTab || (targetTabId != null && activeTab.id !== targetTabId)) {
    throw new Error('The video tab is no longer active. Reopen the extension and try again.');
  }

  const screenshotUrl = await chrome.tabs.captureVisibleTab(windowId, { format: 'png' });
  const screenshotBlob = await (await fetch(screenshotUrl)).blob();
  const bitmap = await createImageBitmap(screenshotBlob);
  const viewportWidth = Number(crop.viewport_width);
  const viewportHeight = Number(crop.viewport_height);
  if (!viewportWidth || !viewportHeight) throw new Error('Video viewport dimensions are missing.');

  const cropValues = [crop.x, crop.y, crop.width, crop.height].map(Number);
  if (!cropValues.every(Number.isFinite) || cropValues[2] <= 0 || cropValues[3] <= 0) {
    throw new Error('Video/image crop dimensions are invalid.');
  }
  const [cropX, cropY, cropWidth, cropHeight] = cropValues;
  const scaleX = bitmap.width / viewportWidth;
  const scaleY = bitmap.height / viewportHeight;
  const sourceX = Math.max(0, Math.min(bitmap.width - 1, Math.round(cropX * scaleX)));
  const sourceY = Math.max(0, Math.min(bitmap.height - 1, Math.round(cropY * scaleY)));
  const sourceWidth = Math.max(1, Math.min(bitmap.width - sourceX, Math.round(cropWidth * scaleX)));
  const sourceHeight = Math.max(1, Math.min(bitmap.height - sourceY, Math.round(cropHeight * scaleY)));
  const resize = Math.min(1, maxDimension / Math.max(sourceWidth, sourceHeight));
  const outputWidth = Math.max(1, Math.round(sourceWidth * resize));
  const outputHeight = Math.max(1, Math.round(sourceHeight * resize));
  const canvas = new OffscreenCanvas(outputWidth, outputHeight);
  const context = canvas.getContext('2d', { alpha: false });
  if (!context) throw new Error('Could not prepare the video frame for analysis.');
  context.drawImage(bitmap, sourceX, sourceY, sourceWidth, sourceHeight, 0, 0, outputWidth, outputHeight);
  bitmap.close();

  const jpeg = await canvas.convertToBlob({ type: 'image/jpeg', quality: maxDimension <= 224 ? 0.48 : 0.55 });
  if (!jpeg.size || jpeg.size > 512 * 1024) throw new Error('Captured video frame exceeded the analysis size limit.');
  const bytes = new Uint8Array(await jpeg.arrayBuffer());
  let binary = '';
  for (let offset = 0; offset < bytes.length; offset += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(offset, Math.min(offset + 0x8000, bytes.length)));
  }
  return `data:image/jpeg;base64,${btoa(binary)}`;
}

async function captureVideoCropSequence(windowId, targetTabId, crop, existingFrames = [], targetCount = 10) {
  const frames = [...existingFrames].slice(0, targetCount);
  while (frames.length < targetCount) {
    const captureStarted = Date.now();
    try {
      const frame = await captureVideoCrop(windowId, targetTabId, crop, 224);
      if (!frame) break;
      frames.push(frame);
    } catch (e) {
      break;
    }
    if (frames.length >= targetCount) break;
    const waitMs = Math.max(0, 550 - (Date.now() - captureStarted));
    if (waitMs > 0) await new Promise((resolve) => setTimeout(resolve, waitMs));
  }
  return frames;
}

async function prepareVisualPayload(payload, windowId, targetTabId, requestType) {
  const prepared = { ...payload };
  const crop = prepared.video_crop || prepared.image_crop;
  const videoIsPlaying = prepared.video_is_playing === true;
  prepared.video_context = requestType === 'ANALYZE_VIDEO_FEED' || prepared.video_context === true;
  delete prepared.video_crop;
  delete prepared.image_crop;
  delete prepared.image_url;
  delete prepared.video_is_playing;

  if (requestType === 'ANALYZE_VIDEO_FEED' && crop && videoIsPlaying &&
      (!prepared.video_frame_data_urls || prepared.video_frame_data_urls.length < 10)) {
    try {
      prepared.video_frame_data_urls = await captureVideoCropSequence(windowId, targetTabId, crop, prepared.video_frame_data_urls || [], 10);
      if (prepared.video_frame_data_urls.length) {
        prepared.frame_data_url = prepared.video_frame_data_urls[prepared.video_frame_data_urls.length - 1];
      }
    } catch (err) {
      console.warn('MediaTrust could not capture reel frame sequence:', err);
    }
  } else if (!prepared.frame_data_url && crop) {
    try {
      prepared.frame_data_url = await captureVideoCrop(windowId, targetTabId, crop);
    } catch (err) {
      console.warn('MediaTrust could not capture the visible media frame:', err);
    }
  }
  return prepared;
}

// Centralized Message Dispatcher
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  (async () => {
    const { settings } = await chrome.storage.local.get(['settings']);
    const backendUrl = settings?.backendUrl || DEFAULT_SETTINGS.backendUrl;

    try {
      if (request.type === 'ANALYZE_PAGE') {
        const windowId = request.windowId ?? sender.tab?.windowId;
        const targetTabId = request.tabId ?? sender.tab?.id;
        const payload = await prepareVisualPayload(request.payload || {}, windowId, targetTabId, request.type);
        const res = await fetch(`${backendUrl}/analyze/page`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        sendResponse({ success: true, data });
      } else if (request.type === 'ANALYZE_URL') {
        const res = await fetch(`${backendUrl}/analyze/url`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(request.payload),
        });
        const data = await res.json();
        sendResponse({ success: true, data });
      } else if (request.type === 'ANALYZE_VIDEO_FEED') {
        // Prefer a same-origin canvas frame, then fall back to a cropped browser capture.
        const windowId = request.windowId ?? sender.tab?.windowId;
        const targetTabId = request.tabId ?? sender.tab?.id;
        const payload = await prepareVisualPayload(request.payload || {}, windowId, targetTabId, request.type);
        const res = await fetch(`${backendUrl}/analyze/page`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        sendResponse({ success: true, data });
      } else if (request.type === 'CHECK_HEALTH') {
        const res = await fetch(`${backendUrl}/health`);
        const data = await res.json();
        sendResponse({ success: true, data });
      } else {
        sendResponse({ success: false, error: 'Unknown message type' });
      }
    } catch (err) {
      sendResponse({ success: false, error: err.message || 'Network connection failed' });
    }
  })();
  return true; // Keep message channel open for async response
});
