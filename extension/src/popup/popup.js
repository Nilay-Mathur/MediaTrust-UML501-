// MediaTrust Popup Controller

document.addEventListener('DOMContentLoaded', async () => {
  const statusBadge = document.getElementById('status-badge');
  const statusDot = document.getElementById('status-dot');
  const statusText = document.getElementById('status-text');
  const activeHostEl = document.getElementById('active-host');
  const btnAnalyzePage = document.getElementById('btn-analyze-page');
  const btnAnalyzeReel = document.getElementById('btn-analyze-reel');
  const resultBox = document.getElementById('result-box');
  const resRiskLabel = document.getElementById('res-risk-label');
  const resScoreBadge = document.getElementById('res-score-badge');
  const resSummary = document.getElementById('res-summary');
  const resMediaVerdict = document.getElementById('res-media-verdict');
  const btnFullReport = document.getElementById('btn-full-report');
  const linkOptions = document.getElementById('link-options');

  let currentTab = null;

  function pageUrlForAnalysis(value) {
    try { const url = new URL(value); return url.origin + url.pathname; } catch { return ''; }
  }

  // 1. Check active tab
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs && tabs[0]) {
      currentTab = tabs[0];
      try {
        const url = new URL(currentTab.url);
        activeHostEl.innerText = url.hostname;
      } catch {
        activeHostEl.innerText = currentTab.url || 'Unknown page';
      }
    }
  });

  // 2. Health check to backend
  chrome.runtime.sendMessage({ type: 'CHECK_HEALTH' }, (res) => {
    if (res?.success) {
      statusDot.className = 'status-dot online';
      statusText.innerText = 'Connected';
    } else {
      statusDot.className = 'status-dot offline';
      statusText.innerText = 'Offline';
    }
  });

  // 3. Analyze Page Action
  btnAnalyzePage.addEventListener('click', () => {
    if (!currentTab) return;
    btnAnalyzePage.disabled = true;
    btnAnalyzePage.innerText = 'Analyzing page heuristics...';

    chrome.tabs.sendMessage(
      currentTab.id,
      { type: 'EXTRACT_PAGE_CONTENT' },
      (contentRes) => {
        if (contentRes?.error) {
          btnAnalyzePage.disabled = false;
          btnAnalyzePage.innerText = 'Inspect Current Page';
          alert(contentRes.error);
          return;
        }
        const payload = {
          url: pageUrlForAnalysis(currentTab.url),
          page_title: currentTab.title,
          text_content: contentRes?.text || '',
          links: contentRes?.links || [],
          image_crop: contentRes?.image_crop || null,
          video_context: Boolean(contentRes?.video_context),
        };

        chrome.runtime.sendMessage({ type: 'ANALYZE_PAGE', payload, windowId: currentTab.windowId, tabId: currentTab.id }, (res) => {
          btnAnalyzePage.disabled = false;
          btnAnalyzePage.innerText = 'Inspect Current Page';

          if (res?.success && res.data) {
            displayResult(res.data);
          } else {
            alert(res?.error || 'Unable to connect to MediaTrust backend.');
          }
        });
      }
    );
  });

  // 4. Analyze Active Reel Action
  btnAnalyzeReel.addEventListener('click', () => {
    if (!currentTab) return;
    btnAnalyzeReel.disabled = true;
    btnAnalyzeReel.innerText = 'Sampling reel frames...';

    chrome.tabs.sendMessage(currentTab.id, { type: 'CAPTURE_ACTIVE_VIDEO_FRAME' }, (captureRes) => {
      if (chrome.runtime.lastError || captureRes?.error) {
        btnAnalyzeReel.disabled = false;
        btnAnalyzeReel.innerText = 'Check Active Video / Reel';
        alert(captureRes?.error || 'Could not read the active tab. Refresh it and try again.');
        return;
      }

      const payload = {
        url: pageUrlForAnalysis(currentTab.url),
        page_title: currentTab.title,
        text_content: captureRes?.text_content || '',
        links: captureRes?.links || [],
        frame_data_url: captureRes?.frame_data_url || null,
        video_frame_data_urls: captureRes?.video_frame_data_urls || [],
        video_context: true,
        video_is_playing: Boolean(captureRes?.video_is_playing),
        video_crop: captureRes?.video_crop || null,
      };

      chrome.runtime.sendMessage({
        type: 'ANALYZE_VIDEO_FEED',
        payload,
        windowId: currentTab.windowId,
        tabId: currentTab.id,
      }, (res) => {
        btnAnalyzeReel.disabled = false;
        btnAnalyzeReel.innerText = 'Check Active Video / Reel';

        if (res?.success && res.data) {
          displayResult(res.data);
        } else {
          alert(res?.error || 'Unable to connect to MediaTrust backend.');
        }
      });
    });
  });

  // 5. Options link
  linkOptions.addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
  });

  function displayResult(data) {
    resultBox.style.display = 'block';

    const colors = {
      low: { bg: '#ecfdf5', text: '#047857', border: '#10b981' },
      moderate: { bg: '#fffbeb', text: '#b45309', border: '#f59e0b' },
      high: { bg: '#fff1f2', text: '#be123c', border: '#f43f5e' },
      critical: { bg: '#ffe4e6', text: '#9f1239', border: '#e11d48' },
    }[data.overall_risk] || { bg: '#f1f5f9', text: '#334155', border: '#94a3b8' };

    resScoreBadge.style.background = colors.bg;
    resScoreBadge.style.color = colors.text;

    const imageResult = data.detector_results?.image_detector;
    const videoResult = data.detector_results?.video_detector;
    const deepfakeResult = data.detector_results?.deepfake_video_detector;
    const textResult = data.detector_results?.text_detector;

    const vidScore = Number(videoResult?.aggregate_ai_score ?? 0);
    const vidThreshold = Math.max(0.85, Number(videoResult?.ai_decision_threshold ?? 0.85));
    const hasVidAi = videoResult?.status === 'completed' && Number(videoResult.frames_analyzed || 0) >= 10 && videoResult.ai_alert_enabled !== false && vidScore >= vidThreshold;

    const imgScore = Number(imageResult?.ai_generated_score ?? 0);
    const imgThreshold = Math.max(0.85, Number(imageResult?.ai_decision_threshold ?? 0.85));
    const hasImgAi = imageResult?.status === 'completed' && !videoResult && imgScore >= imgThreshold;

    const dfScore = Number(deepfakeResult?.fake_probability ?? 0);
    const dfThreshold = Math.max(0.85, Number(deepfakeResult?.decision_threshold ?? 0.85));
    const hasDf = deepfakeResult?.status === 'completed' && deepfakeResult.face_crops_applied === true && Number(deepfakeResult.face_frames_detected || 0) >= 10 && dfScore >= dfThreshold;

    let mediaSignal = null;
    if (hasDf) {
      mediaSignal = { positive: true, text: `🎭 Face-manipulated deepfake detected: ${(dfScore * 100).toFixed(1)}% model probability across sampled face frames.` };
    } else if (hasVidAi) {
      mediaSignal = { positive: true, text: `🤖 AI-generated video detected: ${(vidScore * 100).toFixed(1)}% synthetic probability (peak frame: ${(Number(videoResult.peak_frame_score) * 100).toFixed(1)}%).` };
    } else if (hasImgAi) {
      mediaSignal = { positive: true, text: `🤖 AI-generated image detected: ${(imgScore * 100).toFixed(1)}% model confidence.` };
    } else if (videoResult?.status === 'inconclusive') {
      mediaSignal = { positive: false, text: `No AI verdict: ${videoResult.error || 'not enough video frames were sampled.'}` };
    } else if (videoResult?.status === 'completed') {
      mediaSignal = { positive: false, text: `✅ Video frames appear authentic (${(vidScore * 100).toFixed(1)}% synthetic score, below ${(vidThreshold * 100).toFixed(0)}% threshold).` };
    } else if (imageResult?.status === 'completed') {
      mediaSignal = { positive: false, text: `✅ Image appears authentic (${((1 - imgScore) * 100).toFixed(1)}% authentic score).` };
    }

    if (mediaSignal) {
      resMediaVerdict.hidden = false;
      resMediaVerdict.className = `media-verdict ${mediaSignal.positive ? 'ai-signal' : 'no-signal'}`;
      resMediaVerdict.innerText = mediaSignal.text;
    } else {
      resMediaVerdict.hidden = true;
      resMediaVerdict.innerText = '';
    }

    // Set risk label and score
    if (data.classification_tag === 'ai_generated' || hasVidAi || hasImgAi || hasDf) {
      resRiskLabel.innerText = 'AI-GENERATED MEDIA';
      const aiVal = Math.round((hasDf ? dfScore : (hasVidAi ? vidScore : imgScore)) * 100);
      resScoreBadge.innerText = `${aiVal}% AI`;
    } else if (data.classification_tag === 'scam' || data.overall_risk === 'high' || data.overall_risk === 'critical') {
      resRiskLabel.innerText = `${data.overall_risk.toUpperCase()} SCAM RISK`;
      resScoreBadge.innerText = `${data.risk_score}/100`;
    } else if (data.classification_tag === 'impersonation') {
      resRiskLabel.innerText = 'IMPERSONATION DETECTED';
      resScoreBadge.innerText = `${data.risk_score}/100`;
    } else {
      resRiskLabel.innerText = `${data.overall_risk.toUpperCase()} RISK`;
      resScoreBadge.innerText = `${data.risk_score}/100`;
    }

    const details = [data.summary || 'Content analysis complete.'];

    if (textResult?.status === 'completed' && textResult.predicted_category !== 'benign') {
      details.push(`Text Analysis: Identified patterns of "${textResult.predicted_category}" with ${(Number(textResult.confidence) * 100).toFixed(1)}% model confidence.`);
    }

    const findings = Array.isArray(data.findings) ? data.findings : [];
    const importantFindings = findings.filter(f => ['moderate', 'high', 'critical'].includes(f.severity));
    if (importantFindings.length > 0) {
      details.push('Key Security Findings:\n' + importantFindings.map(f => `• ${f.description}`).join('\n'));
    }

    resSummary.innerText = details.join('\n\n');
    btnFullReport.href = `http://localhost:5173/analysis/${data.analysis_id}`;
  }
});
