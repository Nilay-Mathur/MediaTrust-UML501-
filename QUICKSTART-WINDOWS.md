# MediaTrust local quick start (Windows)

This bundle includes the website, FastAPI backend, Chrome/Edge extension, EfficientNet-B0 image checkpoint, and scam/phishing text-classifier artifact. No training is needed just to run it. Model scores are dataset-dependent signals, not proof.

## Start the backend

Open PowerShell in this `MediaTrustFinal` folder and run:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

If PowerShell blocks activation in this window, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate again. Keep this window open. Check `http://127.0.0.1:8000/health` or `/docs`.

## Start the website

Open a second PowerShell window in the project folder:

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173`.

## Activate the extension

1. Open `chrome://extensions` in Chrome or `edge://extensions` in Edge.
2. Turn on **Developer mode**.
3. Select **Load unpacked** and choose this project's `extension` folder.
4. Open or refresh the social page. Click the MediaTrust toolbar icon. Use **Inspect Current Page** for page text/links and **Check Active Video / Reel** while the reel is playing. The extension captures 20 sequential frames for face-deepfake analysis and scores those frames with the image model. If Instagram blocks canvas access, it falls back to paced browser screenshots; leave the popup open while it samples.
5. After changing extension files, click **Reload** on its card and refresh the social page.

Keep both servers running. A successful backend connection is shown in the extension popup. Video-canvas access can fail on cross-origin/DRM-protected players or hidden/paused videos. In that case, the extension uses a paced screenshot sequence from the visible video area. Keep the reel playing and leave the popup open; collecting 20 frames can take about 10 seconds. It does not infer visual content from the reel URL.

## What the supplied model metrics mean

- `backend/models/checkpoints/image_metrics.json` reports CIFAKE held-out metrics. CIFAKE contains CIFAR-10 images and Stable-Diffusion-generated images, which differ from current social media photos and reels. The model may miss AI content or flag edited/filtered real media.
- `backend/models/checkpoints/text_classifier_external_metrics.json` reports a held-out SMS spam dataset. It is not a social-post AI-writing detector.
- The scam risk score and visual AI-media score are separate. AI-looking content alone is not evidence of a scam.

For exact retraining commands and dataset layout, see `docs/training-guide.md`. For the six uploaded archives' contents and why only some code/data could be used, see `docs/third-party-integration-audit.md`.


## After adding the ResNeXt-LSTM detector

Restart the backend so it loads `backend/models/checkpoints/resnext50_lstm_deepfake.pt`. Then open `chrome://extensions`, click **Reload** on MediaTrust, and refresh Instagram. No retraining is required for this checkpoint. On first startup, watch the backend log for `Loaded ResNeXt50-LSTM deepfake checkpoint`.
