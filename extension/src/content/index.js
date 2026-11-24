// MediaTrust Content Script: Real-Time Reel & Video Safety Monitor

(function () {
  let settings = {
    autoPageMonitor: true,
    autoVideoMonitor: true,
    hideLowRisk: true,
    debounceMs: 500,
    enabledSites: ['instagram.com', 'youtube.com', 'tiktok.com', 'facebook.com', 'x.com', 'localhost'],
  };

  const analyzedVideos = new Set();
  let currentActiveVideo = null;
  let debounceTimer = null;
  let pageScanTimer = null;
  let lastAutoPageSignature = '';
  let lastAutoPageScanAt = 0;
  let shadowRoot = null;
  let notificationHost = null;
  const AUTO_PAGE_SCAN_COOLDOWN_MS = 5000;

  // Load user settings
  chrome.storage.local.get(['settings'], (res) => {
    if (res.settings) {
      settings = { ...settings, ...res.settings };
    }
    initObserver();
  });

  // Message listener for popup and background actions
  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (isMediaTrustInternalApp()) {
      if (msg.type === 'EXTRACT_PAGE_CONTENT' || msg.type === 'CAPTURE_ACTIVE_VIDEO_FRAME') {
        sendResponse({ error: 'MediaTrust audit pages are excluded from analysis.' });
        return false;
      }
      return false;
    }

    if (msg.type === 'EXTRACT_PAGE_CONTENT') {
      if (isPrivateSurface()) {
        sendResponse({ error: 'MediaTrust skips inbox, message, and chat pages.' });
        return false;
      }
      const text = document.body ? document.body.innerText.slice(0, 5000) : '';
      const links = Array.from(document.querySelectorAll('a[href]'))
        .filter((a) => a.getClientRects().length && a.href.startsWith('http'))
        .slice(0, 5)
        .map((a) => scrubUrl(a.href))
        .filter(Boolean);
      const image = getLargestVisibleImage();
      sendResponse({ text, links, image_crop: getImageCrop(image), video_context: isVideoPageContext() });
      return false;
    }
    if (msg.type === 'CAPTURE_ACTIVE_VIDEO_FRAME') {
      const video = getLargestVisibleVideo();
      if (!video) {
        sendResponse({ error: 'No visible video frame found. Open a Reel, start playback, and try again.' });
        return false;
      }
      const container = getReelContainer(video);
      const videoCrop = getVideoCrop(video);
      const still = captureVideoFrameSized(video, 224);

      sendResponse({
        frame_data_url: still,
        video_frame_data_urls: still ? [still] : [],
        video_context: true,
        video_is_playing: !video.paused && !video.ended,
        video_crop: videoCrop,
        text_content: container ? container.innerText.slice(0, 2000) : '',
        links: container ? Array.from(container.querySelectorAll('a[href]')).slice(0, 5).map((a) => scrubUrl(a.href)).filter(Boolean) : [],
      });
      return false;
    }
    if (msg.type === 'DISPLAY_NOTIFICATION' && msg.payload) {
      handleAnalysisResult(msg.payload);
      sendResponse({ received: true });
      return false;
    }
  });

  function scrubUrl(value) {
    try { const url = new URL(value); return url.origin + url.pathname; } catch { return ''; }
  }

  function isPrivateSurface() {
    return /\/(messages?|messaging|inbox|mail|direct|chat|dm|conversations?)(\/|$)/i.test(window.location.pathname);
  }

  function isVideoPageContext() {
    const host = window.location.hostname.toLowerCase();
    const path = window.location.pathname.toLowerCase();
    const knownVideoRoute = (host.endsWith('instagram.com') && /\/(reel|reels|tv)\//.test(path)) ||
      ((host.endsWith('youtube.com') || host.endsWith('youtu.be')) && /\/(watch|shorts|live)\/?/.test(path)) ||
      (host.endsWith('tiktok.com') && path.includes('/video/')) ||
      (host.endsWith('facebook.com') && /\/(reel|watch)\//.test(path));
    if (knownVideoRoute) return true;
    return Array.from(document.querySelectorAll('video')).some((video) => {
      const rect = video.getBoundingClientRect();
      const style = window.getComputedStyle(video);
      return rect.width >= 100 && rect.height >= 100 && style.display !== 'none' && style.visibility !== 'hidden';
    });
  }

  // Detect and exclude MediaTrust's own web app / dashboard to prevent self-analysis
  function isMediaTrustInternalApp() {
    const href = window.location.href.toLowerCase();
    const host = window.location.hostname.toLowerCase();
    const port = window.location.port;
    const path = window.location.pathname.toLowerCase();

    // Allow test_feed.html for feed simulation testing
    if (href.includes('test_feed.html')) {
      return false;
    }

    // MediaTrust web frontend / dashboard ports on localhost or 127.0.0.1
    if ((host === 'localhost' || host === '127.0.0.1') && (port === '5173' || port === '3000' || port === '8000')) {
      return true;
    }

    // MediaTrust app routes
    if (path.startsWith('/analysis/') || path.startsWith('/history') || path.startsWith('/workspace') || path.startsWith('/models')) {
      return true;
    }

    // Check DOM title and application markers
    if (document.title.toLowerCase().includes('mediatrust') && !href.includes('test_feed')) {
      return true;
    }

    return false;
  }

  function isSiteSupported() {
    if (isMediaTrustInternalApp()) return false;
    if (window.location.protocol === 'file:') return true;
    const host = window.location.hostname.toLowerCase();
    if (!host || host === '127.0.0.1' || host === 'localhost') return true;
    return settings.enabledSites.some((site) => host === site || host.endsWith('.' + site));
  }

  function initObserver() {
    if (isMediaTrustInternalApp() || !isSiteSupported() || isPrivateSurface()) return;

    // Observe scroll / visibility for reels
    if (settings.autoVideoMonitor) {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting && entry.intersectionRatio >= 0.45) {
              handleVideoVisible(entry.target);
            }
          });
        },
        { threshold: [0.45, 0.75] }
      );

      document.querySelectorAll('video').forEach((vid) => observer.observe(vid));

      const domObserver = new MutationObserver((mutations) => {
        for (const m of mutations) {
          for (const node of m.addedNodes) {
            if (node.nodeType === 1) {
              if (node.tagName === 'VIDEO') {
                observer.observe(node);
              } else if (node.querySelectorAll) {
                node.querySelectorAll('video').forEach((v) => observer.observe(v));
              }
            }
          }
        }
      });
      domObserver.observe(document.body, { childList: true, subtree: true });

      // Also listen to window scroll to catch active centered reel
      window.addEventListener('scroll', () => {
        if (debounceTimer) clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          const video = getLargestVisibleVideo();
          if (video && video !== currentActiveVideo) {
            handleVideoVisible(video);
          }
        }, 400);
      }, { passive: true });
    }

    if (settings.autoPageMonitor) {
      scheduleAutoPageScan(2000);
    }
  }

  function scheduleAutoPageScan(delay = settings.debounceMs) {
    if (isMediaTrustInternalApp() || !settings.autoPageMonitor || isPrivateSurface()) return;
    if (pageScanTimer) clearTimeout(pageScanTimer);
    pageScanTimer = setTimeout(() => {
      pageScanTimer = null;
      analyzeVisiblePage(true);
    }, delay);
  }

  function analyzeVisiblePage(automatic = false) {
    if (isMediaTrustInternalApp() || isPrivateSurface()) return;
    const text = document.body ? document.body.innerText.slice(0, 5000) : '';
    const links = Array.from(document.querySelectorAll('a[href]'))
      .filter((a) => a.getClientRects().length && a.href.startsWith('http'))
      .slice(0, 5)
      .map((a) => scrubUrl(a.href))
      .filter(Boolean);
    if (!text && !links.length) return;

    const pageUrl = scrubUrl(window.location.href);
    const pageTitle = document.title.slice(0, 200);
    const image = getLargestVisibleImage();
    const imageUrl = image?.currentSrc || '';
    const imageCrop = getImageCrop(image);
    const signature = `${pageUrl}\n${pageTitle}\n${text.slice(0, 200)}\n${links.join('\n')}\n${imageUrl}`;
    if (automatic) {
      if (signature === lastAutoPageSignature) return;
      const cooldownRemaining = AUTO_PAGE_SCAN_COOLDOWN_MS - (Date.now() - lastAutoPageScanAt);
      if (lastAutoPageScanAt && cooldownRemaining > 0) {
        scheduleAutoPageScan(cooldownRemaining);
        return;
      }
      lastAutoPageSignature = signature;
      lastAutoPageScanAt = Date.now();
    }

    chrome.runtime.sendMessage({
      type: 'ANALYZE_PAGE',
      payload: { url: pageUrl, page_title: pageTitle, text_content: text, links, image_crop: imageCrop, video_context: isVideoPageContext() },
    }, (res) => {
      if (res?.success && res.data) handleAnalysisResult(res.data);
      else if (automatic) lastAutoPageSignature = '';
    });
  }

  function getReelContainer(videoEl) {
    return videoEl.closest('article, [role="article"], .reel, .reel-container, .ytd-reel-video-renderer, [data-e2e="recommend-list-item-container"], div.x1ey2m1c, section') || videoEl.parentElement;
  }

  function handleVideoVisible(videoEl) {
    if (isMediaTrustInternalApp()) return;
    if (currentActiveVideo === videoEl) return;
    currentActiveVideo = videoEl;

    const rect = videoEl.getBoundingClientRect();
    const videoKey = videoEl.currentSrc || videoEl.src || `${window.location.href}#${videoEl.id || Math.round(rect.top + window.scrollY)}`;
    if (analyzedVideos.has(videoKey)) return;

    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      if (currentActiveVideo === videoEl) {
        analyzedVideos.add(videoKey);
        analyzeActiveReel(videoEl);
      }
    }, settings.debounceMs || 500);
  }

  function getLargestVisibleVideo() {
    return Array.from(document.querySelectorAll('video'))
      .map((video) => {
        const rect = video.getBoundingClientRect();
        const style = window.getComputedStyle(video);
        const width = Math.max(0, Math.min(rect.right, window.innerWidth) - Math.max(rect.left, 0));
        const height = Math.max(0, Math.min(rect.bottom, window.innerHeight) - Math.max(rect.top, 0));
        return { video, rect, style, area: width * height };
      })
      .filter(({ video, style, area }) => video.videoWidth > 0 && video.videoHeight > 0 && area > 100 * 100 &&
        style.display !== 'none' && style.visibility !== 'hidden' && Number(style.opacity || 1) > 0)
      .sort((a, b) => b.area - a.area)[0]?.video || null;
  }

  function getVideoCrop(videoEl) {
    const rect = videoEl.getBoundingClientRect();
    const left = Math.max(0, rect.left);
    const top = Math.max(0, rect.top);
    const right = Math.min(window.innerWidth, rect.right);
    const bottom = Math.min(window.innerHeight, rect.bottom);
    if (right <= left || bottom <= top) return null;
    return {
      x: left,
      y: top,
      width: right - left,
      height: bottom - top,
      viewport_width: window.innerWidth,
      viewport_height: window.innerHeight,
    };
  }

  function getLargestVisibleImage() {
    const selectors = 'article img, [role="article"] img, [role="dialog"] img, main img, img';
    return Array.from(document.querySelectorAll(selectors))
      .map((image) => ({ image, rect: image.getBoundingClientRect() }))
      .filter(({ image, rect }) => image.complete && image.naturalWidth >= 160 && image.naturalHeight >= 160 &&
        rect.width >= 120 && rect.height >= 120 && rect.bottom > 0 && rect.right > 0 &&
        rect.top < window.innerHeight && rect.left < window.innerWidth)
      .sort((a, b) => (b.rect.width * b.rect.height) - (a.rect.width * a.rect.height))[0]?.image || null;
  }

  function getImageCrop(imageEl) {
    if (!imageEl) return null;
    const rect = imageEl.getBoundingClientRect();
    const left = Math.max(0, rect.left);
    const top = Math.max(0, rect.top);
    const right = Math.min(window.innerWidth, rect.right);
    const bottom = Math.min(window.innerHeight, rect.bottom);
    if (right <= left || bottom <= top) return null;
    return {
      x: left,
      y: top,
      width: right - left,
      height: bottom - top,
      viewport_width: window.innerWidth,
      viewport_height: window.innerHeight,
    };
  }

  function captureVideoFrameSized(videoEl, maxDimension = 384) {
    if (!videoEl.videoWidth || !videoEl.videoHeight || videoEl.readyState < 2) return null;
    try {
      const scale = Math.min(1, maxDimension / Math.max(videoEl.videoWidth, videoEl.videoHeight));
      const canvas = document.createElement('canvas');
      canvas.width = Math.max(1, Math.round(videoEl.videoWidth * scale));
      canvas.height = Math.max(1, Math.round(videoEl.videoHeight * scale));
      const context = canvas.getContext('2d', { alpha: false });
      if (!context) return null;
      context.drawImage(videoEl, 0, 0, canvas.width, canvas.height);
      return canvas.toDataURL('image/jpeg', 0.65);
    } catch {
      // Cross-origin video may taint canvas; background handles visual crop
      return null;
    }
  }

  async function analyzeActiveReel(videoEl) {
    if (isMediaTrustInternalApp()) return;
    try {
      const container = getReelContainer(videoEl);
      const visibleText = container ? container.innerText.substring(0, 2000) : '';
      const videoCrop = getVideoCrop(videoEl);
      const fastFrame = captureVideoFrameSized(videoEl, 224);
      const videoFrameDataUrls = fastFrame ? [fastFrame] : [];

      const links = [];
      if (container) {
        container.querySelectorAll('a[href]').forEach((a) => {
          const href = a.getAttribute('href');
          if (href && href.startsWith('http')) {
            const clean = scrubUrl(href);
            if (clean && !links.includes(clean)) links.push(clean);
          }
        });
      }

      chrome.runtime.sendMessage(
        {
          type: 'ANALYZE_VIDEO_FEED',
          payload: {
            url: scrubUrl(window.location.href),
            page_title: document.title,
            text_content: visibleText,
            frame_data_url: fastFrame,
            video_frame_data_urls: videoFrameDataUrls,
            video_context: true,
            video_is_playing: !videoEl.paused && !videoEl.ended,
            video_crop: videoCrop,
            links: links.slice(0, 5),
          },
        },
        (res) => {
          if (res?.success && res.data) {
            handleAnalysisResult(res.data, videoEl);
          }
        }
      );
    } catch (err) {
      console.warn('MediaTrust reel observer error:', err);
    }
  }

  // ONLY give popups for AI-generated media and scams!
  function handleAnalysisResult(data, targetVideoEl = null) {
    if (!data || isMediaTrustInternalApp()) return;

    const vidRes = data.detector_results?.video_detector;
    const imgRes = data.detector_results?.image_detector;
    const dfRes = data.detector_results?.deepfake_video_detector;
    const txtRes = data.detector_results?.text_detector;

    const videoThreshold = Math.max(0.85, Number(vidRes?.ai_decision_threshold || 0.85));
    const imageThreshold = Math.max(0.85, Number(imgRes?.ai_decision_threshold || 0.85));
    const deepfakeThreshold = Math.max(0.85, Number(dfRes?.decision_threshold || 0.85));
    const isAi =
      (vidRes?.status === 'completed' && Number(vidRes.frames_analyzed || 0) >= 10 && vidRes.ai_alert_enabled !== false && Number(vidRes.aggregate_ai_score) >= videoThreshold) ||
      (imgRes?.status === 'completed' && !vidRes && !isVideoPageContext() && Number(imgRes.ai_generated_score) >= imageThreshold) ||
      (dfRes?.status === 'completed' && dfRes.face_crops_applied === true && Number(dfRes.face_frames_detected || 0) >= 10 && Number(dfRes.fake_probability) >= deepfakeThreshold);

    const isScam = data.classification_tag === 'scam' ||
      data.classification_tag === 'impersonation' ||
      ['high', 'critical'].includes(String(data.overall_risk).toLowerCase()) ||
      (txtRes?.status === 'completed' && ['scam_fraud', 'phishing_credential_theft', 'impersonation'].includes(txtRes.predicted_category) && Number(txtRes.confidence) >= 0.60);

    // CRITICAL REQUIREMENT: ONLY show popup if it is AI-generated media or a scam!
    // Silent for authentic, normal, or benign reels/pages.
    if (!isAi && !isScam) {
      return;
    }

    renderFloatingNotification(data, targetVideoEl, { isAi, isScam });
  }

  function ensureShadowRoot() {
    if (!notificationHost) {
      notificationHost = document.createElement('div');
      notificationHost.id = 'mediatrust-floating-observer-root';
      document.body.appendChild(notificationHost);
      shadowRoot = notificationHost.attachShadow({ mode: 'open' });
    }
    return shadowRoot;
  }

  function renderFloatingNotification(data, targetVideoEl = null, flags = {}) {
    if (isMediaTrustInternalApp()) return;
    const root = ensureShadowRoot();
    const findings = Array.isArray(data.findings) ? data.findings : [];

    const isAi = Boolean(flags.isAi);
    const isImpersonation = data.classification_tag === 'impersonation';

    // Theme configuration: ONLY AI-Generated or Scam/Threat
    let theme = {
      border: '#ef4444',
      badgeBg: '#fee2e2',
      badgeText: '#991b1b',
      glow: 'rgba(239, 68, 68, 0.35)',
      icon: '🚨',
      title: 'Scam / Threat Alert'
    };

    if (isAi) {
      theme = {
        border: '#f59e0b',
        badgeBg: '#fef3c7',
        badgeText: '#92400e',
        glow: 'rgba(245, 158, 11, 0.35)',
        icon: '🤖',
        title: 'AI-Generated Reel Detected'
      };
    } else if (isImpersonation) {
      theme = {
        border: '#a855f7',
        badgeBg: '#f3e8ff',
        badgeText: '#6b21a8',
        glow: 'rgba(168, 85, 247, 0.35)',
        icon: '🎭',
        title: 'Impersonation Alert'
      };
    }

    // Determine primary score badge
    let scoreDisplay = `${data.risk_score || 0}/100`;
    const vidRes = data.detector_results?.video_detector;
    const imgRes = data.detector_results?.image_detector;
    const dfRes = data.detector_results?.deepfake_video_detector;
    if (isAi) {
      const aiScore = vidRes?.aggregate_ai_score ?? imgRes?.ai_generated_score ?? dfRes?.fake_probability;
      if (Number.isFinite(Number(aiScore))) {
        scoreDisplay = `${(Number(aiScore) * 100).toFixed(0)}% AI`;
      }
    }

    // Format prominent evidence description
    let topFindingText = data.summary;
    const alertFindings = findings.filter((f) => ['moderate', 'high', 'critical'].includes(f.severity));
    if (alertFindings.length > 0) {
      topFindingText = alertFindings.map((f) => f.description).join(' • ');
    }

    const card = document.createElement('section');
    card.setAttribute('role', 'status');
    card.style.cssText = `
      position: fixed;
      right: 20px;
      bottom: 20px;
      width: min(350px, calc(100vw - 32px));
      background: #0f172a;
      color: #f8fafc;
      border: 1.5px solid ${theme.border};
      border-radius: 14px;
      box-shadow: 0 12px 30px rgba(0,0,0,0.5), 0 0 15px ${theme.glow};
      font: 13px/1.5 system-ui, -apple-system, sans-serif;
      z-index: 2147483647;
      overflow: hidden;
      animation: mtFadeIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    `;

    if (!shadowRoot.querySelector('style')) {
      const styleEl = document.createElement('style');
      styleEl.textContent = `
        @keyframes mtFadeIn {
          from { opacity: 0; transform: translateY(12px) scale(0.97); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
      `;
      shadowRoot.appendChild(styleEl);
    }

    const header = document.createElement('div');
    header.style.cssText = 'padding: 12px 14px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; font-weight: 700;';

    const titleEl = document.createElement('div');
    titleEl.style.cssText = 'display: flex; align-items: center; gap: 8px; font-size: 13px;';
    titleEl.innerHTML = `<span>${theme.icon}</span> <span>${theme.title}</span>`;

    const scoreBadge = document.createElement('span');
    scoreBadge.textContent = scoreDisplay;
    scoreBadge.style.cssText = `border-radius: 999px; padding: 2px 10px; font-size: 11px; font-weight: 800; background: ${theme.badgeBg}; color: ${theme.badgeText}; white-space: nowrap;`;
    header.append(titleEl, scoreBadge);

    const body = document.createElement('div');
    body.style.cssText = 'padding: 12px 14px; color: #cbd5e1; font-size: 12px; max-height: 120px; overflow-y: auto; line-height: 1.45;';
    body.textContent = topFindingText || 'MediaTrust real-time social feed safety evaluation.';

    const footer = document.createElement('div');
    footer.style.cssText = 'padding: 10px 14px; background: #020617; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #1e293b;';

    const reportLink = document.createElement('a');
    reportLink.textContent = 'Full Analysis →';
    reportLink.href = `http://localhost:5173/analysis/${encodeURIComponent(String(data.analysis_id || ''))}`;
    reportLink.target = '_blank';
    reportLink.rel = 'noopener noreferrer';
    reportLink.style.cssText = 'color: #38bdf8; font-weight: 600; text-decoration: none; font-size: 12px;';

    const dismissBtn = document.createElement('button');
    dismissBtn.type = 'button';
    dismissBtn.textContent = '✕ Dismiss';
    dismissBtn.style.cssText = 'color: #94a3b8; background: transparent; border: 0; cursor: pointer; font-size: 12px; padding: 4px 6px;';
    dismissBtn.onclick = () => card.remove();

    footer.append(reportLink, dismissBtn);
    card.append(header, body, footer);
    root.replaceChildren(card);
  }
})();
