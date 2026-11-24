# MediaTrust model cards

## Text scam/phishing classifier

- **Architecture:** TF-IDF word unigrams/bigrams plus Logistic Regression.
- **Input:** visible message or page text supplied to the local API.
- **Labels:** labels present in the training CSV. The supplied UCI conversion creates only `benign` and `scam_fraud`; it does not train phishing/impersonation classes.
- **Training:** use `backend/scripts/train_text_classifier.py`; splits are group-held-out. The selected regularization setting uses validation macro-F1; the test partition is used only for final reporting.
- **Artifact:** set `TEXT_MODEL_PIPELINE` in `backend/.env`. The training command writes a versioned external artifact without replacing the included legacy artifact.
- **Current status:** TF-IDF + Logistic Regression artifact is included and configured.
- **Metrics:** the accompanying report covers a held-out SMS spam dataset only; it does not establish detection quality on current social media messages.
- **Limitations:** text can be translated, paraphrased, or crafted to evade lexical patterns; benign urgency can be flagged; probabilities are not calibrated probabilities of fraud.

## AI-generated image classifier

- **Architecture:** EfficientNet-B0 with a two-class head and Grad-CAM visualization.
- **Input:** one image or a small JPEG frame sampled from a visible video.
- **Labels:** `real_image`, `ai_generated`.
- **Training:** use the manifest and group split commands in `docs/training-guide.md`, then `backend/scripts/train_image_classifier_v2.py`.
- **Current status:** EfficientNet-B0 checkpoint is included and configured for single images and sampled video frames.
- **Metrics:** its report states roughly 95.4% held-out accuracy on CIFAKE. CIFAKE does not represent Instagram reels, current generators, or heavy social compression; those numbers are not a real-world guarantee.
- **Limitations:** a source/generator held-out evaluation is needed to assess generalization. Compression, resizing, editing, and unseen generators can change results. Grad-CAM shows model activations; it does not prove that a highlighted region is an AI artifact.


## Face-deepfake video classifier

- **Architecture:** ResNeXt50 frame encoder + LSTM sequence classifier, based on the uploaded detector's training notebook.
- **Input:** 20 sequential frames, resized to 112×112 with ImageNet normalization; the adapter uses OpenCV Haar face crops when a face is found and otherwise uses the full frame.
- **Labels:** class 0 is FAKE, class 1 is REAL, as described by the supplied prediction notebook.
- **Artifact:** `backend/models/checkpoints/resnext50_lstm_deepfake.pt`; loaded tensor-only with strict state-dictionary matching. The checkpoint contains no LSTM bias tensors, so the adapter configures the LSTM without biases to match the actual artifact.
- **Scope and limits:** this is a face-manipulation detector, not a general detector for fully AI-generated scenes, animals, or animation. The source archive did not include a reproducible held-out report or repository-level license. Do not redistribute the checkpoint until its license/terms are clarified. Social compression, new manipulation methods, and non-face clips can reduce reliability. The result is informational, never scam evidence.

## URL analyzer

This component uses lexical rules rather than a trained classifier. It checks URL structure and a short list of patterns. It does not establish that a site is safe or malicious, and the score is not a probability.
