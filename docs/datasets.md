# Datasets & Experimental Data Documentation

This document describes the datasets, expected folder structures, licenses, and preprocessing pipelines used in MediaTrust.

---

## 1. Image Classification Benchmark Datasets

### 1.1 Recommended Public Datasets
- **CIFAKE (Real and AI-Generated Synthetic Images)**:
  - **Source**: Kaggle / Open Data
  - **License**: CC BY-SA 4.0
  - **Size**: 60,000 synthetic images generated via Stable Diffusion 1.4 and 60,000 real images from CIFAR-10.
  - **Intended Use**: Benchmark training and evaluation of binary synthetic image classifiers.

- **GenImage (A Million-Scale Benchmark for AI-Generated Image Detection)**:
  - **Source**: OpenGVLab / NeurIPS 2023
  - **License**: Research & Educational Use
  - **Size**: 1,000,000+ images spanning Midjourney, Stable Diffusion v1.4/v1.5, DALL-E 2, VQDM, and BigGAN.

### 1.2 Local Sample Fixtures
For reproducible testing and local development, MediaTrust bundles labeled synthetic fixtures in `datasets/sample_data/`:
```
datasets/sample_data/
├── real/
│   ├── real_00.jpg ... real_09.jpg
└── ai_generated/
    ├── ai_00.jpg ... ai_09.jpg
```
These can be generated or refreshed anytime via:
```bash
python backend/scripts/generate_sample_fixtures.py
```

---

## 2. Text Classification Datasets

### 2.1 Public Phishing and Fraud Corpora
- **Nazario Phishing Corpus**: Publicly accessible archive of confirmed phishing email bodies and credential harvesting lures.
- **Enron Email Corpus (Benign Communication Baseline)**: Non-malicious corporate correspondence used for benign class calibration.
- **SMS Spam Collection**: Curated collection of 5,574 SMS messages labeled as ham and spam.

### 2.2 Bundled Supervised Corpus
MediaTrust's baseline model is trained on a 40-sample balanced reference corpus representing:
- `benign` (10 samples)
- `scam_fraud` (10 samples)
- `phishing_credential_theft` (10 samples)
- `impersonation` (10 samples)

Model training and serialization are automated in `backend/app/ml/text_detector/service.py` and evaluated in `backend/scripts/evaluate_models.py`.
