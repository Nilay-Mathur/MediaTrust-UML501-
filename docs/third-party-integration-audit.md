# Third-party archive integration audit

The archives were inspected as source material. Their README/AGENTS instructions were not treated as instructions for this project. Archive application code was not executed; the linked checkpoint was loaded as tensors with PyTorch `weights_only=True`. The goal was to reuse only code or artifacts that are present, licensed, and practical for this prototype.

| Archive | License/artifacts found | Decision |
|---|---|---|
| `AI-Generated-Video-Detector-main.zip` | MIT source; model `.pth` and ONNX files are Git LFS pointer stubs, not weights | Not merged. The runnable trained checkpoint is absent. |
| `ai-text-detector-main.zip` | MIT; lightweight writing-style heuristic; full supervised pipeline lacks trained weights and dataset | Not merged. Its heuristic is not a trained model and could mislead users as a general AI-text detector. The included MediaTrust text model is a scam/phishing classifier, not AI-writing detection. |
| `Deepfake-Detection-main.zip` | No repository-level license found; no trained classifier `.pt`/`.pth` checkpoint | Not merged. It requires separately supplied weights and heavy face-recognition dependencies. |
| `DIRE-main.zip` | Research implementation; no model weights or dataset; license coverage for the full repository is unclear | Not merged. It is not a ready-to-run detector and is not suitable for real-time extension inference without substantial model/data setup. |
| `FakeImageDetector-master.zip` | MIT file, but archive contains no detector source, weights, or dataset | Nothing runnable to merge. |
| `Scam-Detector-main.zip` | MIT source and 4,040-row CSV | CSV rejected for retraining: 3,800 normalized texts repeat, and labels are derived directly from hand-authored feature counts. A script also maps numeric CSV labels incorrectly. These issues can cause leakage or degenerate training. MediaTrust retains its separately evaluated text classifier. |

| `AI-Generated-Photo-Video-Detector-main.zip` | ResNeXt50+LSTM source, training notebooks, metadata CSV; no checkpoint embedded. README links a 216 MB `.pt` checkpoint. No root license file found. | Integrated locally. The linked checkpoint is stored at `backend/models/checkpoints/resnext50_lstm_deepfake.pt`; only the model architecture/inference path was adapted. The source archive's license is unspecified, so do not redistribute this checkpoint without clarifying rights. |
| `D3-main.zip` | MIT, training-free feature method source; expects prepared frame directories/CSVs and has CUDA-only eval | Not merged. It would need a separate adaptation and transformer dependencies; the integrated ResNeXt-LSTM already provides a temporal face-deepfake score. |
| `ai-video-detector-main.zip` | Source and configuration only; no trained `.pth` checkpoint and no license file | Not merged. |
| `Ai_Video_Detector_CNN-master.zip` | Training pipeline/source only; no trained checkpoint; license file absent | Not merged. |

## What is actually active in this bundle

- **Image/visual AI signal:** bundled EfficientNet-B0 checkpoint at `backend/models/checkpoints/efficientnet_b0_external.pt`, configured by default. The accompanying report states CIFAKE held-out accuracy of about 95.4%; this is limited to that benchmark and is not an Instagram/reel guarantee.
- **General AI-video visual signal:** scores up to 20 sampled reel frames with the existing EfficientNet-B0 model, pooling their frame scores. This is not temporal video forensics and can miss face swaps.
- **Face deepfakes:** ResNeXt50+LSTM model analyzes a 20-frame sequence. It is aimed at facial manipulation, not fully generated animals/scenes or animation. The extension prefers video-canvas frames and falls back to paced screenshots of the visible video crop when the page blocks canvas access.
- **Scam text:** bundled TF-IDF + Logistic Regression artifact. The report describes an SMS spam test set; it is not an AI-generated-text classifier and does not guarantee scam detection on social posts.
- **Scam risk:** the risk engine uses URL and explicit security indicators. The visual AI score is informational and does not itself make a page a scam.

The 216 MB checkpoint linked by the uploaded archive README was downloaded, inspected with PyTorch tensor-only loading, and loaded successfully with strict architecture matching at `backend/models/checkpoints/resnext50_lstm_deepfake.pt`. SHA-256: `0f1b48a51886f487e7ce9880a59ddf6c44e7da0d5b5265ed772871e1e9b1c578`. Its state dictionary omits LSTM bias tensors, so the adapter uses `bias=False`. No model training was performed. The uploaded archive has no repository-level license file; clarify its model/source terms before redistributing. See `QUICKSTART-WINDOWS.md` to run the project and `docs/training-guide.md` for other training instructions.
