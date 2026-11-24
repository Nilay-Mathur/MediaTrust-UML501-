document.addEventListener('DOMContentLoaded', () => {
  const backendUrlInput = document.getElementById('backend-url');
  const autoMonitorInput = document.getElementById('auto-monitor');
  const hideLowRiskInput = document.getElementById('hide-low-risk');
  const debounceInput = document.getElementById('debounce-ms');
  const btnSave = document.getElementById('btn-save');
  const statusMsg = document.getElementById('status-msg');

  chrome.storage.local.get(['settings'], (res) => {
    const s = res.settings || {};
    backendUrlInput.value = s.backendUrl || 'http://127.0.0.1:8000/api/v1';
    autoMonitorInput.checked = s.autoVideoMonitor !== false;
    hideLowRiskInput.checked = s.hideLowRisk !== false;
    debounceInput.value = s.debounceMs || 500;
  });

  btnSave.addEventListener('click', () => {
    const updated = {
      backendUrl: backendUrlInput.value.trim(),
      autoVideoMonitor: autoMonitorInput.checked,
      hideLowRisk: hideLowRiskInput.checked,
      debounceMs: parseInt(debounceInput.value, 10) || 500,
      enabledSites: ['instagram.com', 'youtube.com', 'tiktok.com', 'facebook.com', 'x.com', 'localhost'],
    };

    chrome.storage.local.set({ settings: updated }, () => {
      statusMsg.style.display = 'block';
      setTimeout(() => statusMsg.style.display = 'none', 3000);
    });
  });
});
