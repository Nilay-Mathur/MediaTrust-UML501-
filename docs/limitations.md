# MediaTrust System Limitations & Responsible AI Statement

In accordance with ethical machine learning and cybersecurity engineering practices, MediaTrust documents known technical boundaries, model uncertainties, and responsible-use guidelines.

---

## 1. Machine Learning Boundaries

1. **Statistical Association vs Ground-Truth Fact**:
   Deep learning computer vision models (such as EfficientNet-B0) identify statistical texture distributions characteristic of generative synthesis. A high AI-generated score indicates visual similarity to trained diffusion/GAN patterns; it does not constitute legal proof that an image was artificially generated.

2. **Compression and Social Media Filtering Noise**:
   Platforms such as Instagram, TikTok, and WhatsApp apply aggressive lossy compression and re-encoding. Compression artifacts can degrade high-frequency synthetic signatures, potentially causing false negatives on low-bitrate deepfakes or false positives on heavily filtered genuine photographs.

3. **Facial Deepfake Swaps vs General Generative Synthesis**:
   The current image model evaluates general synthetic texture anomalies across the entire frame. If an attacker performs a localized face-swap on a high-resolution authentic photograph, whole-image texture analysis may not always isolate the face boundary unless fine-tuned specifically on landmark-aligned facial datasets (e.g. FaceForensics++).

4. **Natural Urgency in Benign Text**:
   The text classifier identifies urgency and financial pressure tactics. Authentic business emails containing critical deadlines (e.g. "Submit quarterly tax reports by 5 PM today") may score elevated urgency risk despite being benign. Contextual human review remains essential.

---

## 2. Security & Network Boundaries

1. **HTTPS and Certificate Limitations**:
   MediaTrust explicitly clarifies that the presence of an active HTTPS certificate does not prove a website is legitimate. Modern phishing kits routinely acquire free Let's Encrypt certificates.

2. **Cryptographic Hashes (SHA-256)**:
   A matching SHA-256 hash proves only that the digital file bitstream has not been modified since the reference hash was computed. It does not prove that the underlying photograph depicts real-world truth.

3. **Missing Metadata**:
   Most social media platforms automatically strip EXIF metadata for user privacy. Therefore, the absence of camera EXIF data is never treated as proof of malicious manipulation.

---

## 3. Future Scope & Roadmap

- **Phase 2 Multimodal Vision-Language**: Integration of CLIP/BLIP zero-shot vision-language models for cross-modal consistency checking between video frames and spoken audio transcripts.
- **Phase 3 C2PA Provenance Standards**: Native parsing and validation of C2PA (Coalition for Content Provenance and Authenticity) cryptographic manifest assertions.
- **Phase 4 Temporal 3D-CNN / Video Transformers**: Adding a temporal 3D-ResNet or VideoMAE model to directly capture motion blur consistency across consecutive video frames.


## Temporal reel and face-deepfake limits

MediaTrust now has a ResNeXt50+LSTM face-manipulation checkpoint and samples a 20-frame sequence from a playing browser video when canvas access is permitted. This model is aimed at manipulated human faces, not fully AI-generated scenes, animals, or animation. The checkpoint's source archive did not include a reproducible evaluation report or clear license. If video canvas access is blocked, the extension falls back to paced screenshots of the visible video crop to build a temporal sequence; this takes about 10 seconds and requires the reel to remain visible and playing. Uploaded video analysis through the website can use the backend video decoder instead.
