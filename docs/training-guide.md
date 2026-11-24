# MediaTrust model training guide

## Current state

The project bundle includes configured image and text model artifacts, so you do not need to train just to run the app. The image checkpoint is EfficientNet-B0; its companion metrics report a CIFAKE held-out test accuracy of about 95.4%. The text classifier is TF-IDF + Logistic Regression; its report covers an SMS spam dataset. These reports are limited to their stated test sets and do not establish performance on Instagram, current generators, edited photos, or modern social scams.

The raw training datasets are not included in this delivery. To retrain reproducibly, obtain the datasets described below and keep train/validation/test sources separate. The old `train_image_classifier.py` script is a tiny fixture trainer and is not the recommended training path; use `train_image_classifier_v2.py` as described below. A ResNeXt50+LSTM face-deepfake checkpoint from the uploaded photo/video detector is already configured at `backend/models/checkpoints/resnext50_lstm_deepfake.pt`; no retraining is needed to use it. Its source archive did not include a license file or reproducible evaluation report. See `third-party-integration-audit.md` for details. The additional uploaded video-detector zips did not provide other usable trained weights.

## 1. Install the backend (Windows PowerShell)

Open PowerShell in the MediaTrust\backend folder:

~~~powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
~~~

If PowerShell blocks activation, run Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass in that PowerShell window, then activate. A CUDA-enabled PyTorch install is optional; CPU training works but takes longer.

## 2. Train scam/phishing text screening

### Get the starter corpus

Download the official [UCI SMS Spam Collection](https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip) and extract it under MediaTrust\datasets\raw\sms\. It has ham/spam SMS labels under CC BY 4.0. It is an educational binary baseline; it does not label phishing versus impersonation and it is not a representative modern social-media scam dataset.

From MediaTrust\backend, convert the UCI file and train:

~~~powershell
python scripts/prepare_uci_sms.py --input ..\datasets\raw\sms\SMSSpamCollection --output ..\datasets\processed\sms_messages.csv
python scripts/train_text_classifier.py --input-csv ..\datasets\processed\sms_messages.csv
~~~

The converter maps ham to benign and spam to scam_fraud. It hashes normalized message text into a group ID so exact duplicate messages stay in one split. The trainer creates group-held-out train, validation, and test partitions, selects Logistic Regression C by validation macro-F1, refits on train plus validation, then evaluates the test set once. It writes:

- backend\models\checkpoints\text_classifier_external.joblib
- backend\models\checkpoints\text_classifier_external_metrics.json

This does not overwrite the bundled legacy artifact. Add this line to backend\.env to activate the trained classifier:

~~~text
TEXT_MODEL_PIPELINE=models/checkpoints/text_classifier_external.joblib
~~~

Restart the backend. The UCI dataset has only two categories. For the prototype's four-category taxonomy, collect and label additional examples as phishing_credential_theft and impersonation, include independent campaign/source group IDs, then rerun the trainer. Do not infer those labels from the binary SMS label.

### CSV format for your own labeled messages

Required header:

~~~csv
text,label,group
"Please verify your account at the included link",phishing_credential_theft,campaign_001
"Your package will arrive tomorrow",benign,conversation_041
~~~

Use benign, scam_fraud, phishing_credential_theft, or impersonation as labels. Use a group ID for the source, campaign, sender/template family, or duplicate family. Do not put duplicates or lightly rewritten campaign messages in different groups. The trainer refuses small training data by default; --allow-small-demo only allows a smoke run and labels the resulting report small_demo_only.

## 3. Train AI-image screening

The [CIFAKE source repository](https://github.com/jordan-bird/CIFAKE-Real-and-AI-Generated-Synthetic-Images) describes a benchmark built from CIFAR-10 real images and Stable Diffusion 1.4 generated images and points to its Kaggle distribution. The source repository states MIT licensing; verify that statement and Kaggle terms when downloading. This is an educational benchmark, not proof of detection on modern photographs, other generators, edited images, or social-media compression.

Download and extract CIFAKE so the folders look like:

~~~text
datasets/raw/CIFAKE/
  train/REAL/
  train/FAKE/
  test/REAL/
  test/FAKE/
~~~

From MediaTrust\backend, create a manifest, group-isolated splits, then train:

~~~powershell
python scripts/prepare_cifake_manifest.py --dataset-root ..\datasets\raw\CIFAKE --output ..\datasets\processed\cifake_manifest.csv
python scripts/prepare_splits.py --input-csv ..\datasets\processed\cifake_manifest.csv --output-dir ..\datasets\processed\cifake_splits
python scripts/train_image_classifier_v2.py --split-dir ..\datasets\processed\cifake_splits --epochs 5 --batch-size 16
~~~

The manifest hashes each image so byte-identical duplicates cannot cross splits. The split tool requires path,label,group columns and every class in each partition. The trainer selects the best checkpoint by validation loss, then chooses an AI score threshold on validation data with a measured false-positive rate at or below 5%. It reports that threshold and validation recall/FPR, class-wise test metrics, and ROC-AUC. A source/generator-held-out evaluation is still needed to assess generalization; CIFAKE alone cannot establish that claim.

The output checkpoint is backend\models\checkpoints\efficientnet_b0_external.pt; metrics are written to backend\models\checkpoints\image_metrics.json. Add this line to backend\.env to activate the model:

~~~text
IMAGE_MODEL_CHECKPOINT=models/checkpoints/efficientnet_b0_external.pt
~~~

Restart the backend. The included image checkpoint is configured by default. Face-deepfake sequence analysis uses the separate ResNeXt-LSTM checkpoint and requires 20 readable video frames; this is not a general fully-generated-video detector.

## 4. Run the extension locally

In a second PowerShell window, from MediaTrust\backend:

~~~powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
~~~

In Chrome or Edge, open chrome://extensions or edge://extensions, enable Developer mode, choose Load unpacked, and select the MediaTrust\extension directory. For the local feed demo, open PowerShell in the extension folder, run python -m http.server 8090, then visit http://localhost:8090/test_feed.html.

AI-media popups use an 85% minimum model score for image, reel, and face-deepfake findings. Reel alerts also require at least 10 sampled frames; a still frame cannot count as a reel verdict. Reel alerts are enabled at that cutoff by default; the bundled image model is not validated on Instagram reels, so an 85% score can still be wrong and lower-scoring AI reels will be missed. Validate on labeled, platform-compressed real and AI reels with creator/generator-separated splits before making accuracy claims.

The extension waits until a video is substantially visible, samples one downscaled frame when canvas access is allowed, and sends it with visible surrounding text and up to three visible links to the local backend. Cross-origin video may block frame capture; text and URL checks still run. The backend never downloads the video URL. Automatic checks run on enabled sites, skip common inbox/chat paths, and show a popup for moderate or higher risk. URLs have query strings and fragments removed before analysis.

## How to judge the result

Read the generated JSON report. Prefer macro-F1, per-class precision/recall, confusion matrix, PR-AUC for imbalanced scam data, and calibration/threshold behavior to raw accuracy. Check test size and group overlap. These metrics describe only the dataset and split that produced them. Set alert thresholds using validation data and a measured false-positive budget before making strong safety claims. The overall risk score is heuristic, not a calibrated probability.
