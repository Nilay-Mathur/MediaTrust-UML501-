import os
import re
from typing import Dict, Any, List, Tuple
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from app.core.config import settings
from app.core.logging import logger

TAXONOMY = ["benign", "scam_fraud", "phishing_credential_theft", "impersonation"]

# Seed dataset of labeled security messages to ensure the supervised pipeline is immediately functional and reproducible
SEED_DATA = [
    # Benign messages
    ("Hey Sarah, let's catch up for lunch tomorrow around 1 PM at the café.", "benign"),
    ("Your meeting with the project team has been scheduled for Thursday at 10 AM on Zoom.", "benign"),
    ("Thanks for your order! Your package has shipped and tracking information is available in your account.", "benign"),
    ("Reminder: Dentist appointment tomorrow at 3:30 PM. Please call if you need to reschedule.", "benign"),
    ("Hi Mom, I landed safely in Chicago. Will call you once I check into the hotel.", "benign"),
    ("Please find attached the minutes from yesterday's computer science seminar.", "benign"),
    ("Weekly library newsletter: New books on artificial intelligence and algorithms now available.", "benign"),
    ("Can you review the pull request on GitHub when you get a chance? No rush.", "benign"),
    ("Happy birthday David! Hope you have a wonderful day celebrating with family.", "benign"),
    ("The university IT department has completed scheduled network maintenance. All systems are normal.", "benign"),

    # Scam / Fraud messages
    ("CONGRATULATIONS! You have won $1,000,000 in the International Lottery! Send your bank details immediately to claim.", "scam_fraud"),
    ("Guaranteed daily return of 15% on your crypto investment! Deposit Bitcoin to our VIP trading wallet today.", "scam_fraud"),
    ("URGENT: Your parcel delivery is pending unpaid customs fees of $2.99. Pay immediately to avoid package return.", "scam_fraud"),
    ("Work from home and earn $500/day with just 30 minutes on Telegram! DM our agent now for instant signup bonus.", "scam_fraud"),
    ("You have an unclaimed inheritance of 4.5 million USD from a deceased relative. Reply with your passport copy.", "scam_fraud"),
    ("Make easy money fast with our binary options algorithm. 100% win rate guaranteed. Send wire transfer.", "scam_fraud"),
    ("Exclusive loan offer approved! 0% interest rate for 12 months. Wire processing fee of $150 via Western Union.", "scam_fraud"),
    ("You were selected for a $500 Amazon Gift Card! Click link and enter your phone number to receive voucher code.", "scam_fraud"),
    ("Claim your government stimulus check now before the funds expire at midnight. Enter your social security number.", "scam_fraud"),
    ("Your crypto wallet has received 2.45 ETH. Pay 0.05 ETH transaction gas fee to unlock your funds.", "scam_fraud"),

    # Phishing / Credential theft
    ("URGENT: Your Netflix subscription has expired. Update your billing credit card details within 24 hours to avoid suspension.", "phishing_credential_theft"),
    ("Security Alert: Unauthorized login attempt detected from Russia. Verify your Apple ID password here immediately.", "phishing_credential_theft"),
    ("Your Chase Bank account is temporarily locked due to suspicious activity. Sign in to reactivate your online access.", "phishing_credential_theft"),
    ("Google Workspace: Your email storage is 99% full. Click here to confirm your password and upgrade storage.", "phishing_credential_theft"),
    ("PayPal Alert: You sent a payment of $649.99 to an unknown merchant. If this was not you, log in to dispute immediately.", "phishing_credential_theft"),
    ("Microsoft 365: Your account password expires in 2 hours. Keep your current password by clicking the verification link.", "phishing_credential_theft"),
    ("Bank of America: A wire transfer of $4,200 is pending. Enter your PIN and debit card number to confirm or cancel.", "phishing_credential_theft"),
    ("Your Dropbox account will be deleted in 48 hours unless you verify your login credentials on our portal.", "phishing_credential_theft"),
    ("Facebook Security Team: Your page has violated copyright policies. Submit your credentials to avoid permanent deletion.", "phishing_credential_theft"),
    ("DocuSign: Important tax document requires your signature. Log in with your email and password to view document.", "phishing_credential_theft"),

    # Impersonation claims
    ("Hi dad, this is my new phone number. My old phone fell in water. Can you please text me here and transfer $400 for rent?", "impersonation"),
    ("Hello, I am the CEO. I am in a confidential board meeting and need you to urgently purchase five $100 Apple gift cards for clients.", "impersonation"),
    ("Internal Revenue Service (IRS): A federal arrest warrant has been issued in your name. Call this agent immediately to settle.", "impersonation"),
    ("This is Inspector Sharma from the Cyber Crime Cell. Your Aadhaar number was found in a money laundering case. Cooperate now.", "impersonation"),
    ("Hi, I am Elon Musk. For the next 30 minutes, I am doubling all Bitcoin sent to this official promotional address.", "impersonation"),
    ("Your HR Director here. We are auditing payroll records today. Reply with your banking details and W-2 form immediately.", "impersonation"),
    ("This is technical support from Microsoft Windows. We detected a Trojan virus transmitting data from your IP address.", "impersonation"),
    ("Hey buddy, lost my wallet and passport while traveling in London. Could you send me $500 via Zelle? Will pay back Monday.", "impersonation"),
    ("Instagram Verification Badge Support: You have been approved for a verified blue tick. Send your account password to claim.", "impersonation"),
    ("Federal Express Executive Office: A high-value diplomatic pouch registered to your name requires customs tax settlement.", "impersonation"),
]

def preprocess_text(text: str) -> str:
    """Preprocesses text while preserving security-relevant tokens and symbols."""
    t = text.lower()
    # Normalize excessive whitespace
    t = re.sub(r'\s+', ' ', t).strip()
    return t

class TextDetectorService:
    def __init__(self):
        self.pipeline: Pipeline = None
        self.model_loaded = False
        self.pipeline_path = settings.TEXT_MODEL_PIPELINE
        self.model_version = "text-seed-demo-40-v1"
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        try:
            if os.path.exists(self.pipeline_path):
                logger.info(f"Loading text classifier artifact from {self.pipeline_path}")
                self.pipeline = joblib.load(self.pipeline_path)
                self.model_version = getattr(self.pipeline, "mediatrust_model_version_", "text-tfidf-logreg-legacy-unverified")
                self.model_loaded = True
            else:
                logger.warning("No trained text artifact found. Using the 40-example seed model in memory (DEMO ONLY); see backend/scripts/train_text_classifier.py.")
                self._train_and_persist(SEED_DATA)
        except Exception as e:
            logger.error(f"Failed to initialize text detector: {str(e)}")
            self.model_loaded = False

    def _train_and_persist(self, data: List[Tuple[str, str]]):
        X = [preprocess_text(item[0]) for item in data]
        y = [item[1] for item in data]

        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            max_features=5000,
            token_pattern=r'(?u)\b\w+\b|\$|\%'
        )
        classifier = LogisticRegression(C=1.5, max_iter=1000, random_state=42)

        self.pipeline = Pipeline([
            ("vectorizer", vectorizer),
            ("classifier", classifier)
        ])

        self.pipeline.fit(X, y)
        self.model_version = "text-seed-demo-40-v1"
        self.model_loaded = True
        logger.warning("Seed text model is in-memory demo data only; it was not saved as a trained artifact.")

    def predict(self, text: str) -> Dict[str, Any]:
        if not self.model_loaded or self.pipeline is None:
            return {
                "status": "unavailable",
                "error": "Text classification pipeline is not loaded.",
                "predicted_category": "unavailable",
                "probabilities": {},
                "top_features": [],
                "confidence": 0.0,
                "model_version": self.model_version
            }

        try:
            clean_text = preprocess_text(text)
            vectorizer = self.pipeline.named_steps["vectorizer"]
            classifier = self.pipeline.named_steps["classifier"]

            # Probability per class
            probs = self.pipeline.predict_proba([clean_text])[0]
            classes = classifier.classes_
            prob_dict = {str(c): round(float(p), 4) for c, p in zip(classes, probs)}

            predicted_class = str(self.pipeline.predict([clean_text])[0])
            confidence = prob_dict.get(predicted_class, 0.0)

            # Explainability: Extract top contributing n-gram features
            top_features = self._explain_prediction(clean_text, predicted_class, vectorizer, classifier)

            # Heuristic threat pattern flags
            threat_indicators = self._extract_threat_patterns(text)

            return {
                "status": "completed",
                "predicted_category": predicted_class,
                "confidence": confidence,
                "probabilities": prob_dict,
                "top_contributing_features": top_features,
                "threat_indicators": threat_indicators,
                "model_version": self.model_version,
                "limitations": [
                    "Trained on supervised patterns of common fraud, phishing, and impersonation attempts.",
                    "Cannot verify the ground truth authenticity of a sender without verifiable DKIM/DMARC headers.",
                    "Benign messages containing urgency words (e.g. deadlines) may score elevated risk."
                ]
            }
        except Exception as e:
            logger.error(f"Text classifier inference error: {str(e)}")
            return {
                "status": "failed",
                "error": f"Inference failed: {str(e)}",
                "predicted_category": "inconclusive",
                "probabilities": {},
                "top_contributing_features": [],
                "confidence": 0.0,
                "model_version": self.model_version
            }

    def _explain_prediction(self, text: str, predicted_class: str, vectorizer, classifier) -> List[Dict[str, Any]]:
        """Computes feature contribution weights for tokens present in the input text."""
        try:
            classes = list(classifier.classes_)
            if predicted_class not in classes:
                return []
            class_idx = classes.index(predicted_class)
            if classifier.coef_.shape[0] == 1:
                # Binary classification in scikit-learn
                weights = classifier.coef_[0] if class_idx == 1 else -classifier.coef_[0]
            else:
                weights = classifier.coef_[class_idx]

            feature_names = vectorizer.get_feature_names_out()

            # Transform single text
            tfidf_vec = vectorizer.transform([text]).toarray()[0]
            contributions = []

            for idx in np.where(tfidf_vec > 0)[0]:
                feat_name = feature_names[idx]
                score = float(weights[idx] * tfidf_vec[idx])
                if score > 0:
                    contributions.append({
                        "feature": feat_name,
                        "importance": round(score, 4)
                    })

            # If all scores <= 0, still return top non-zero features
            if not contributions:
                for idx in np.where(tfidf_vec > 0)[0]:
                    contributions.append({
                        "feature": feature_names[idx],
                        "importance": round(float(weights[idx] * tfidf_vec[idx]), 4)
                    })

            # Sort by highest contribution
            contributions.sort(key=lambda x: x["importance"], reverse=True)
            return contributions[:8]
        except Exception as exc:
            logger.warning(f"Feature contribution explanation failed: {exc}")
            return []

    def _extract_threat_patterns(self, text: str) -> List[Dict[str, str]]:
        indicators = []
        low_text = text.lower()

        patterns = [
            (r'\b(urgent|immediately|action required|suspended|24 hours|expires today)\b', "Urgency & Coercion", "Message creates artificial time pressure to bypass critical thinking."),
            (r'\b(password|credential|ssn|social security|pin|debit card|cvv|seed phrase)\b', "Sensitive Data Solicitation", "Direct solicitation of credentials or confidential identity secrets."),
            (r'\b(wire transfer|western union|crypto|bitcoin|gift card|zelle|cashapp)\b', "Irreversible Payment Mechanism", "Request to transfer funds via non-refundable or pseudonymous channels."),
            (r'\b(lottery|won|inheritance|unclaimed funds|stimulus|grant|guaranteed return)\b', "Unsolicited Financial Lure", "Promises unrealistic financial gains or prizes."),
            (r'\b(ceo|hr director|inspector|police|irs|fbi|cyber crime)\b', "Authority Figure Claim", "Claims institutional or executive authority to demand compliance."),
        ]

        for regex, title, desc in patterns:
            match = re.search(regex, low_text)
            if match:
                indicators.append({
                    "indicator": title,
                    "matched_sample": match.group(0),
                    "explanation": desc
                })

        return indicators

import numpy as np
text_detector_service = TextDetectorService()
