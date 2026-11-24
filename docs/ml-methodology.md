# Machine Learning Methodology & Evaluation Report

This document details the mathematical formulations, model architectures, training procedures, and interpretability mechanisms implemented across the MediaTrust platform.

---

## 1. Image Classification: EfficientNet-B0 Transfer Learning

### 1.1 Architecture & Compound Scaling
MediaTrust utilizes an **EfficientNet-B0** convolutional neural network backbone pretrained on ImageNet-1K. EfficientNet balances network depth $d$, width $w$, and input image resolution $r$ using a compound scaling coefficient $\phi$:
$$d = \alpha^\phi, \quad w = \beta^\phi, \quad r = \gamma^\phi$$
$$\text{subject to } \alpha \cdot \beta^2 \cdot \gamma^2 \approx 2, \quad \alpha \ge 1, \beta \ge 1, \gamma \ge 1$$

For baseline EfficientNet-B0, $\phi = 1$, setting the input tensor dimension to $224 \times 224 \times 3$.

### 1.2 Fine-Tuning & Classification Head
To adapt the backbone for binary detection (`0: real_image`, `1: ai_generated`), the original 1000-class dense layer is replaced with a customized transfer learning head:
$$\text{Head}(x) = W_2 \cdot \text{ReLU}(W_1 \cdot \text{Dropout}_{0.3}(x)) + b_2$$
where $W_1 \in \mathbb{R}^{128 \times 1280}$ and $W_2 \in \mathbb{R}^{2 \times 128}$.

### 1.3 Loss Function & Optimization
The network is optimized using binary cross-entropy with logit normalization:
$$\mathcal{L}_{\text{CE}} = - \sum_{i=1}^N \left[ y_i \log(\hat{y}_i) + (1 - y_i) \log(1 - \hat{y}_i) \right]$$
using the AdamW optimizer ($\text{lr} = 10^{-4}$, weight decay $= 10^{-4}$).

---

## 2. Visual Explainability: Grad-CAM Formulation

To prevent the image detector from acting as an uninterpretable black box, MediaTrust computes **Gradient-weighted Class Activation Mapping (Grad-CAM)** on the final convolutional layer $A = \text{model.backbone.features[-1]}$.

1. **Neuron Importance Weights**: The gradient of the target class logit $y^c$ ($c = 1$ for `ai_generated`) with respect to feature map activations $A^k$ is pooled globally:
$$\alpha_k^c = \frac{1}{Z} \sum_{i=1}^U \sum_{j=1}^V \frac{\partial y^c}{\partial A_{i,j}^k}$$
where $Z = U \times V$ represents spatial dimensions of the feature map.

2. **Weighted Activation Map**: A rectified linear combination is applied to highlight features that positively contribute to the synthetic classification:
$$L^c_{\text{Grad-CAM}} = \text{ReLU}\left( \sum_k \alpha_k^c A^k \right)$$

3. **Alpha-Blending**: The normalized activation map $L^c$ is interpolated to the original image dimensions and blended with a custom pseudo-color overlay where red denotes highest synthetic artifact density.

---

## 3. Natural Language Processing: TF-IDF + Logistic Regression

### 3.1 Feature Vectorization
Text messages are mapped into high-dimensional sparse representations using $n$-grams ($n \in \{1, 2\}$) with sublinear term-frequency scaling:
$$\text{tf}_{\text{sublinear}}(t, d) = 1 + \log(\text{tf}(t, d)) \quad \text{for } \text{tf} > 0$$
$$\text{idf}(t, D) = \log\left( \frac{1 + |D|}{1 + |\{d \in D : t \in d\}|} \right) + 1$$
$$\text{tfidf}(t, d, D) = \text{tf}_{\text{sublinear}}(t, d) \times \text{idf}(t, D)$$

### 3.2 Multinomial Logistic Regression
The probability that an input text $x$ belongs to threat class $c \in \{\text{benign}, \text{scam\_fraud}, \text{phishing\_credential\_theft}, \text{impersonation}\}$ is modeled via softmax:
$$P(Y = c \mid x) = \frac{\exp(w_c^T x + b_c)}{\sum_{j=1}^K \exp(w_j^T x + b_j)}$$

### 3.3 Explainable Feature Importance
For each prediction, individual token contributions are computed directly:
$$\text{Importance}(t, c) = w_{c, t} \times x_t$$
Top positive terms ($w_{c, t} \cdot x_t > 0$) are surfaced in the audit interface to substantiate the finding.

---

## 4. Temporal Video Sampling & Anomaly Aggregation

Rather than treating frames as independent random variables, MediaTrust extracts frames at a bounded rate ($1.0 \text{ fps}$) and computes a conservative anomaly pooling metric:
$$\text{Score}_{\text{video}} = 0.60 \times \text{Percentile}_{85}(S) + 0.40 \times \text{Mean}(S)$$
where $S = \{s_1, s_2, \dots, s_M\}$ is the sequence of frame synthetic scores.

- **Rationale**: Generative deepfakes in social video feeds frequently exhibit temporal flickering or localized keyframe defects rather than uniform distortion across all seconds. The 85th-percentile weighting captures peak manipulation while dampening single-frame outlier noise.

---

## 5. Centralized Heuristic Risk Engine

Disparate detector scores are normalized into evidence units and evaluated using a multi-factor policy:
$$\text{Risk}_{\text{overall}} = \min\left(100, \; \text{round}\left(0.65 \times \max(R) + 0.35 \times \bar{R}\right)\right)$$
where $R = \{r_1, r_2, \dots, r_m\}$ denotes the set of active detector risk contributions.

- **Low Risk (0–29)**: Standard baseline digital hygiene.
- **Moderate Risk (30–59)**: Minor heuristic triggers or borderline model confidence.
- **High Risk (60–84)**: Strong evidence of synthetic generation or fraudulent solicitation.
- **Critical Risk (85–100)**: Multiple converging threats (e.g. brand impersonation combined with direct credential harvesting).
