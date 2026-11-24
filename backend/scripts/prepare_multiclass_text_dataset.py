"""Prepare a rich 4-class dataset (benign, scam_fraud, phishing_credential_theft, impersonation)
combining SMS messages with social media reel captions, phishing alerts, and impersonation lures.
"""
import csv
import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SMS_PATH = ROOT / "datasets" / "processed" / "sms_messages.csv"
OUT_PATH = ROOT / "datasets" / "processed" / "multiclass_messages.csv"

def make_group(text: str) -> str:
    cleaned = re.sub(r"\W+", " ", text.lower()).strip()[:40]
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()

ADDITIONAL_SAMPLES = [
    # --- Phishing & Credential Theft ---
    ("URGENT: Your Chase Bank account has been locked due to suspicious attempts. Verify password now: http://chase-verify.xyz", "phishing_credential_theft"),
    ("Bank of America Security: Unusual login from IP 192.168.1.1. Enter PIN and online ID here to unlock access.", "phishing_credential_theft"),
    ("Wells Fargo Alert: A wire transfer of $2,450 is pending. If this was not you, confirm debit card details immediately.", "phishing_credential_theft"),
    ("Netflix Support: Your payment method failed and account is suspended. Update billing credit card info within 24 hours.", "phishing_credential_theft"),
    ("Apple ID Verification: Your iCloud storage is restricted. Re-authenticate password to prevent photo loss.", "phishing_credential_theft"),
    ("Google Workspace: Storage quota exceeded 99%. Sign in with email and password to increase quota.", "phishing_credential_theft"),
    ("Microsoft 365: Your password expires today. Click to keep current credentials: http://ms-portal-auth.online", "phishing_credential_theft"),
    ("PayPal Warning: You sent $840 to Coinbase. Click dispute link and log in to cancel transaction immediately.", "phishing_credential_theft"),
    ("DocuSign Notice: Urgent financial document awaits your signature. Enter your email password to decrypt document.", "phishing_credential_theft"),
    ("Instagram Security: Copyright violation reported against your account. Submit login credentials or face permanent ban.", "phishing_credential_theft"),
    ("Amazon Security: An iPhone 15 was ordered on your account. Log in here to cancel unauthorized order: http://amz-login.xyz", "phishing_credential_theft"),
    ("Coinbase Alert: New withdrawal address added. Log in and enter 2FA security code immediately to freeze withdrawal.", "phishing_credential_theft"),
    ("Facebook Community Standards: Your page is scheduled for deletion in 48 hours. Confirm password to appeal.", "phishing_credential_theft"),
    ("Citibank Alert: Debit card deactivated due to ATM fraud. Verify CVV and expiration date to reactivate.", "phishing_credential_theft"),
    ("Dropbox Security: Unrecognized login from Singapore. Please confirm your credentials to protect your cloud files.", "phishing_credential_theft"),
    ("DHL Delivery: Address missing on your shipment. Log in with your email account to verify your delivery address.", "phishing_credential_theft"),
    ("USPS Notification: Parcel delivery failed due to incorrect zip code. Click link and confirm credit card for $0.30 re-delivery.", "phishing_credential_theft"),
    ("Meta Verified Support: You qualify for verified blue tick badge! Enter account username and password to activate.", "phishing_credential_theft"),
    ("Snapchat Team: Suspicious device logged in. Confirm current password and phone number to secure account.", "phishing_credential_theft"),
    ("LinkedIn Talent Solutions: You have 3 urgent job offers. Log in to your professional portal to view contracts.", "phishing_credential_theft"),

    # --- Social Media Reel Scams & Financial Fraud ---
    ("Invest $100 and get guaranteed $1000 daily return using our automated AI trading bot! DM on Telegram for VIP link.", "scam_fraud"),
    ("Crypto Doubler: Send 0.1 BTC to this official wallet address and get 0.2 BTC back in 15 minutes! Limited slots.", "scam_fraud"),
    ("Work from home and make $300-$500 per day simply liking YouTube videos! No experience needed, message on WhatsApp.", "scam_fraud"),
    ("CONGRATULATIONS! You have been selected as the random winner of $50,000 in cash! Send your bank details to claim.", "scam_fraud"),
    ("Binance Giveaway 2026: Deposit Ethereum into the smart contract pool to receive 3x instant airdrop multiplier.", "scam_fraud"),
    ("Federal stimulus check of $1,400 ready for direct deposit! Click link and submit your Social Security number today.", "scam_fraud"),
    ("Unclaimed inheritance of $4.8M USD left by a distant relative. Reply with your passport and bank wire info.", "scam_fraud"),
    ("Binary Options Forex Signals: 99.8% win rate guaranteed. Join our VIP channel and turn $50 into $5,000 this week.", "scam_fraud"),
    ("Instant personal loan approved up to $50,000 with 0% interest! Send $200 processing fee via Western Union or CashApp.", "scam_fraud"),
    ("Free $1,000 Walmart Gift Card! Click link, answer 3 survey questions and enter phone number to redeem voucher code.", "scam_fraud"),
    ("Secret wealth method that banks don't want you to know! Check link in bio to copy my automated crypto trading setup.", "scam_fraud"),
    ("Drop 'WIN' in the comments and I will send $2,000 directly to your CashApp or Zelle right now! Must be following me.", "scam_fraud"),
    ("Exclusive luxury watch giveaway: Pay only $9.95 shipping fee to receive a $500 timepiece. Limited stock remaining.", "scam_fraud"),
    ("Join my private pump and dump signal group. We guarantee 500% profits on the next meme coin launch. Send wire fee.", "scam_fraud"),
    ("Earn passive income without working: Cloud mining contract generates $50 daily Bitcoin payout. Deposit today.", "scam_fraud"),
    ("Amazon Mystery Box returns for only $29! Contains MacBooks, iPhones, and gaming consoles. Order before sellout.", "scam_fraud"),
    ("Government grant assistance: Claim your non-repayable $10,000 business grant. Pay small administrative fee via gift card.", "scam_fraud"),
    ("TikTok Creator Fund Glitch: How I make $10,000/week on autopilot. Buy my secret PDF guide for only $49.", "scam_fraud"),
    ("Your wallet address has received 3.5 USDT. Click here to connect MetaMask and approve unlimited smart contract spending.", "scam_fraud"),
    ("Guaranteed stock trading algorithm with zero risk. Send Bitcoin investment to our registered Swiss portfolio.", "scam_fraud"),

    # --- Impersonation & Social Engineering ---
    ("Hi dad, my phone fell in water and this is my temporary number. Can you urgently wire $450 for my rent today?", "impersonation"),
    ("Hi mom, I lost my wallet while traveling in London. Please transfer $500 to this account so I can pay hotel bill.", "impersonation"),
    ("This is the CEO. I am in an urgent meeting with clients and need you to buy 5 $100 Apple gift cards right away.", "impersonation"),
    ("Internal Revenue Service (IRS): A federal tax fraud warrant has been issued in your name. Call this agent to settle.", "impersonation"),
    ("Inspector Kumar from Cyber Crime Department. Your identity was found in a money laundering case. Cooperate or face arrest.", "impersonation"),
    ("This is Elon Musk. I am giving back to the community by doubling all crypto sent to this official promo address.", "impersonation"),
    ("Microsoft Support Desk: We detected a dangerous Trojan horse virus sending data from your computer. Call immediately.", "impersonation"),
    ("Your HR Manager here: We are updating employee payroll records. Reply with your banking routing number and SSN.", "impersonation"),
    ("FedEx Executive Office: A diplomatic container registered to your name requires immediate customs clearance payment.", "impersonation"),
    ("Bank Fraud Prevention Officer: We blocked an illegal wire. Please read back the 6-digit passcode we just sent to your phone.", "impersonation"),
    ("Hey bro, stranded at the airport without my cards. Can you Zelle me $300? I will pay you back as soon as I land.", "impersonation"),
    ("Amazon Customer Support: An order for $1,299 was placed from Ohio. If this was not you, connect with our technician now.", "impersonation"),
    ("PayPal Fraud Division: Unauthorized transfer detected. Transfer your balance to our safe custody account.", "impersonation"),
    ("FBI Cyber Division: Formal subpoena issued. Do not discuss this with anyone and transfer settlement funds via Bitcoin ATM.", "impersonation"),
    ("MrBeast Official: You won my $100,000 challenge! Send $50 delivery registration fee via CashApp to claim your prize.", "impersonation"),
    ("Taylor Swift VIP Giveaway: Text this number to claim backstage VIP tickets and pass your personal details.", "impersonation"),
    ("Chief Technology Officer: Mandatory security audit. Provide your VPN login credentials so we can patch your workstation.", "impersonation"),
    ("Social Security Administration: Your SSN has been suspended due to criminal activity in Texas. Call officer now.", "impersonation"),
    ("Hi sweetie, Mom here on my new iPad. Can you send $250 via Venmo for grocery delivery? App is acting strange.", "impersonation"),
    ("Office of the President: Confidential corporate acquisition. Wire $15,000 escrow fee immediately to counsel account.", "impersonation"),
    ("United States Postal Inspector: Contraband seized with your delivery address. Contact inspector immediately.", "impersonation"),
    ("Cristiano Ronaldo Official: Congratulations fan! You have been chosen for an autographed jersey. Pay courier shipping.", "impersonation"),
    ("Apple Executive Relations: Tim Cook philanthropy fund. Send wallet address for 2 ETH grant distribution.", "impersonation"),
    ("IT Security Helpdesk: We are performing server migration. Send your corporate email password to avoid account lock.", "impersonation"),
    ("Department of Homeland Security: Customs border inspection notification regarding import parcel. Respond now.", "impersonation"),
    ("Sheriff County Office: Citation for failure to appear for jury duty. Pay $500 electronic bond to avoid arrest warrant.", "impersonation"),
    ("Managing Director: I am boarding a flight and cannot take calls. Purchase five $200 Steam gift cards for the team.", "impersonation"),
    ("Bank of America Fraud Specialist: Suspicious card swipe in Miami. Provide full 16-digit card number to verify identity.", "impersonation"),
    ("WhatsApp Support Agent: Your WhatsApp account will be expired in 24 hours. Send the 6-digit verification code.", "impersonation"),
    ("Google Account Recovery Agent: We received a request to delete your Gmail account. Verify password to stop deletion.", "impersonation"),
    ("Netflix Billing Representative: Your subscription renewal was declined. Read your credit card CVV code over SMS.", "impersonation"),
    ("Hi Grandma, it is your grandson. I was in a car accident and need bail money transferred to the lawyer immediately.", "impersonation"),
    ("Chief Financial Officer: Wire transfer instruction for vendor invoice. Change receiving bank details to this account.", "impersonation"),
    ("Telecom Provider Technical Support: SIM card duplicate request received. Confirm identity with your national ID.", "impersonation"),
    ("Instagram Creator Partnerships: Official collaboration offer for $5,000 per reel. Connect your Instagram via our link.", "impersonation"),
    ("Crypto Exchange Helpdesk: Unusual withdrawal activity. Transfer funds to decentralized cold storage link.", "impersonation"),

    # --- Benign Social Media Captions, Everyday Chat & Messages ---
    ("Golden hour in the Swiss Alps! The autumn colors on this hiking trail were unreal. Highly recommend packing warm boots. #travel #nature", "benign"),
    ("Quick 15-minute high protein pasta recipe! Fresh basil, cherry tomatoes, garlic and olive oil. Save this reel for dinner tonight!", "benign"),
    ("Top 5 Python productivity tips for data science in 2026. Use list comprehensions, itertools, and vectorized numpy operations.", "benign"),
    ("My morning routine before work: 20-minute run, cold shower, fresh pour-over coffee, and 10 pages of reading. What is yours?", "benign"),
    ("Full body dumbbell workout you can do at home in 30 minutes! 4 sets of goblet squats, Romanian deadlifts, and shoulder press.", "benign"),
    ("Exploring Kyoto temples during cherry blossom season. The architecture and tranquil gardens are pure magic. #japan #travel", "benign"),
    ("How electric vehicle batteries actually work: breaking down lithium-ion chemistry, thermal management, and charging curves.", "benign"),
    ("Easy sourdough bread tutorial for beginners. 70% hydration, 4 stretch and folds, overnight cold ferment in the fridge.", "benign"),
    ("Sunset timelapse over the ocean in Maui. Listening to the waves is the most relaxing sound on earth. Have a peaceful weekend!", "benign"),
    ("3 mistakes to avoid when starting your fitness journey: prioritize sleep, track your protein intake, and be consistent.", "benign"),
    ("Hey Sarah, let's meet for lunch at the cafeteria tomorrow around noon. Looking forward to catching up!", "benign"),
    ("The university library will be closed this Sunday for scheduled electrical maintenance. Study rooms reopen Monday morning.", "benign"),
    ("Your package has been delivered to your front porch. Thank you for shopping with us! Tracking receipt attached.", "benign"),
    ("Reminder: Dentist appointment tomorrow at 3:30 PM. Please reply to confirm or call to reschedule.", "benign"),
    ("Please find attached the minutes and slides from yesterday's computer science seminar on neural networks.", "benign"),
    ("Happy birthday David! Wishing you a wonderful year ahead filled with joy, health, and success.", "benign"),
    ("Can you review the pull request on GitHub when you get a chance? No rush, just whenever you have time.", "benign"),
    ("Flight landed safely in Seattle. Taking the light rail to the hotel now, will text you when I arrive.", "benign"),
    ("Weekly team standup meeting rescheduled to Thursday 11 AM due to the company all-hands conference.", "benign"),
    ("The weather forecast predicts sunny skies and 72 degrees this weekend. Perfect day for a bike ride along the river.", "benign"),
]

def main():
    rows = []
    
    # Load SMS messages if available
    if SMS_PATH.exists():
        with open(SMS_PATH, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                text = r.get("text", "").strip()
                label = r.get("label", "").strip()
                group = r.get("group", "").strip() or make_group(text)
                
                # Refine label taxonomy
                if label == "scam_fraud":
                    # Check if it has phishing / credential keywords
                    if re.search(r"\b(password|verify|account|bank|login|pin|cvv|security|card|ssn)\b", text, re.IGNORECASE):
                        label = "phishing_credential_theft"
                    else:
                        label = "scam_fraud"
                elif label not in ("benign", "scam_fraud", "phishing_credential_theft", "impersonation"):
                    label = "benign"
                
                rows.append({"text": text, "label": label, "group": group})
    
    # Add rich multiclass samples
    for text, label in ADDITIONAL_SAMPLES:
        rows.append({"text": text, "label": label, "group": make_group(text)})
    
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label", "group"])
        writer.writeheader()
        writer.writerows(rows)
    
    from collections import Counter
    counts = Counter(r["label"] for r in rows)
    print(f"Created {OUT_PATH} with {len(rows)} samples:")
    for k, v in counts.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
