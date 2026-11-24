# MediaTrust User Guide

Welcome to **MediaTrust: Real-Time Digital Trust and Safety Layer**. This guide provides practical steps for using the website workspace and browser extension.

---

## 1. Web Workspace Navigation

### 1.1 Analyzing an Image for AI Generation
1. Navigate to the **Analysis Workspace** (`/workspace`).
2. Select the **Image Analysis** tab.
3. Drag and drop an image file (JPEG, PNG, or WebP up to 15MB) into the drop zone.
4. *(Optional)* Enter an expected SHA-256 hash to verify whether the file has been altered.
5. Click **Analyze Content**.
6. Review the resulting **Heuristic Risk Score**, **Grad-CAM visual activation overlay**, and **EXIF provenance summary**.
7. Click **View Full Audit Report** for a permanent, exportable record.

### 1.2 Inspecting Suspicious Text & Scam Messages
1. Open the **Text & Scam** tab.
2. Paste the message text (e.g. unsolicited lottery notification, bank suspension warning, crypto bonus claim).
3. *(Optional)* Enter claimed sender organization (e.g. "Chase Bank").
4. Click **Analyze Content**.
5. Observe the predicted intent category (`scam_fraud`, `phishing_credential_theft`, `impersonation`, or `benign`) and the top contributing n-gram words highlighted in blue.

### 1.3 Verifying Suspicious URLs
1. Open the **URL & Phishing** tab.
2. Enter the full target URL (e.g. `http://paypal.com.verify-billing.xyz/login`).
3. Toggle safe network probe if desired.
4. Click **Analyze Content**.
5. Review identified lexical flags (e.g. punycode homoglyphs, deceptive subdomains, non-standard ports).

---

## 2. Chrome / Edge Browser Extension

### 2.1 Real-Time Social Reel & Video Monitor
1. Load the extension unpacked in `chrome://extensions`.
2. Browse social feeds with video reels (e.g. YouTube Shorts, Instagram Reels, or `extension/test_feed.html`).
3. As you pause on an active video, the extension's `IntersectionObserver` automatically analyzes the visible context in the background.
4. If suspicious scam patterns or synthetic indicators are found, a floating notification appears in the **bottom-right corner**.
5. Click **Open Full Audit Report** to view the comprehensive evidence breakdown on the MediaTrust web app.

### 2.2 Extension Popup Fast-Check
1. Click the MediaTrust shield icon in your browser toolbar.
2. Verify that the status dot shows **Connected** (pointing to your local backend API).
3. Click **Inspect Current Page** to quickly evaluate the page title, text, and outbound links.
