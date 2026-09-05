#!/usr/bin/env python3
"""
deal_closer.py - AI Client Cooperation, Objection Handling & Contract Closer.

Handles incoming replies from hotel owners/managers:
  1. Classifies intent (Pricing, OTA objections, Demo request, Skeptical, Ready to close).
  2. Generates cooperative, consultative replies that overcome objections and build trust.
  3. Generates a formal, professional Hotel Website & Direct Booking Agreement ready for signature.

Usage:
  python deal_closer.py reply --id lead-001 --intent price
  python deal_closer.py reply --id lead-001 --intent ota_objection
  python deal_closer.py reply --id lead-001 --text "How much does it cost and how long does it take?"
  python deal_closer.py contract --id lead-001 --price 25000 --currency INR
  python deal_closer.py contract --id lead-001 --price 1200 --currency USD --out contract.md
"""
import argparse, json, os, sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE = os.environ.get("LEADS_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE, "data")
LEADS_FILE = os.path.join(DATA_DIR, "hotel_leads.json")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")


def load_leads():
    if os.path.exists(LEADS_FILE):
        with open(LEADS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def detect_intent(text):
    t = text.lower()
    if any(w in t for w in ["price", "cost", "charge", "rate", "quote", "how much", "budget"]):
        return "price"
    elif any(w in t for w in ["booking.com", "airbnb", "ota", "agoda", "makemytrip", "already get", "enough guests", "busy"]):
        return "ota_objection"
    elif any(w in t for w in ["contract", "agreement", "invoice", "start", "proceed", "ready", "hire", "bank details"]):
        return "contract_ready"
    elif any(w in t for w in ["demo", "mockup", "sample", "preview", "show me", "link", "portfolio"]):
        return "demo_interest"
    elif any(w in t for w in ["don't need", "dont need", "no need", "not interested", "phone only"]):
        return "no_need"
    return "demo_interest"


def generate_cooperative_reply(lead, intent, cfg, custom_note=""):
    hotel_name = lead.get("hotel_name", "your property")
    contact_name = lead.get("contact_name", "there")
    city = lead.get("city", "your area")
    from_name = cfg.get("from_name", "Ahmad Raza")

    if intent == "price":
        subject = f"Re: Website & Booking System for {hotel_name} - Pricing & ROI"
        body = f"""Hi {contact_name},

Thank you for getting back to me! I'm glad to share our straightforward pricing and how quickly it pays for itself.

To make this completely risk-free and high-return for {hotel_name}, we offer two turnkey packages:

  📦 Package 1: Essential Direct Booking & Reviews Suite
  - Custom, mobile-responsive hotel website designed around your photos
  - Zero-commission direct booking engine with instant room reservations
  - Customer Reviews Engine showcasing verified 5-star traveler testimonials
  - Direct payment gateway setup (credit cards / UPI / NetBanking / PayPal)
  - Turnkey delivery in 7–10 days
  👉 Investment: ₹8,000 to ₹9,500 INR (or $99–$120 USD one-time)

  🚀 Package 2: Complete Hospitality Growth Suite (Most Popular)
  - Everything in Package 1, plus:
  - 2-Way Channel Manager sync (instant calendar sync with Booking.com/MakeMyTrip/Airbnb)
  - Automated guest review collection email/SMS after checkout
  - Google Business & Local SEO setup so travelers searching "{city} hotels" find you first
  - 30 days dedicated post-launch support and staff walkthrough
  👉 Investment: ₹12,000 to ₹15,000 INR (or $150–$180 USD one-time)

💡 The ROI Math for {hotel_name}:
If an average stay is ₹2,000 and OTAs charge 18% commission (₹360 per booking), saving just 2 to 3 direct bookings every month completely recovers your entire ₹8,000–₹15,000 investment within 30 days. Every reservation after that is 100% pure profit for {hotel_name}.

Would you like me to send a 3-minute video walkthrough of the booking engine and review showcase, or can we hop on a quick 10-minute call tomorrow?

Best regards,
{from_name}"""

    elif intent == "ota_objection":
        subject = f"Re: Direct Bookings vs OTAs for {hotel_name}"
        body = f"""Hi {contact_name},

I completely understand, and it's fantastic that channels like Booking.com / Airbnb are driving solid occupancy for {hotel_name}!

Our system is actually designed to work *hand-in-hand* with your existing OTAs, not replace them:

1. Capture Repeat Guests at 100% Profit:
   When guests stay with you once and love your hospitality, they usually search for your hotel directly next season. Without your own direct website, they book through Booking.com again — costing you another 18% to 22% in commissions on someone who is already your loyal customer.

2. Social Proof & Verified Review Showcase:
   Over 80% of travelers discover a hotel on an OTA, but then Google the hotel's name to see direct photos and customer reviews. Having your own modern website with integrated customer reviews allows you to capture those guests directly before they look at competing hotels.

3. Complete Calendar Sync:
   Our booking engine syncs automatically with Booking.com and Airbnb calendars via iCal/channel manager, meaning zero double-bookings and zero extra manual work for your staff.

I’d be happy to show you a quick preview of how this works seamlessly without disrupting your current OTA flow. Would you be open to a 5-minute preview link?

Best regards,
{from_name}"""

    elif intent == "demo_interest":
        subject = f"Re: Interactive Demo for {hotel_name} (Direct Booking & Review Engine)"
        body = f"""Hi {contact_name},

Fantastic! I’m excited to show you what we've prepared for {hotel_name}.

Here is what we've tailored for you:
  🏨 Interactive Room Showcase & Direct Reservation Flow
  ⭐ Customer Review Showcase with verified ratings widget
  📱 Seamless Mobile Checkout (fast 2-step booking without third-party fees)

I would love to send over the personalized demo preview and walk through how we can have {hotel_name}'s official site live within 7–10 days.

Are you available for a brief 10-minute Zoom / Google Meet or phone call tomorrow at your convenience? Let me know what time works best for you.

Best regards,
{from_name}"""

    elif intent == "no_need":
        subject = f"Re: Online presence for {hotel_name}"
        body = f"""Hi {contact_name},

Thank you for your honesty, I really appreciate you letting me know!

Many independent hotel owners initially feel that word-of-mouth or phone bookings are enough. However, today over 78% of travelers look up a hotel online on their phone before visiting, specifically looking for:
1. Room photos and transparent pricing.
2. Authentic customer reviews and ratings from past guests.
3. An instant way to confirm their stay without phone tag.

Without a direct site, many of these high-paying guests end up choosing a nearby competitor in {city} simply because they could see reviews and book in 30 seconds.

Even a simple 3-page site with direct bookings and customer reviews typically increases direct revenue by 25–40%.

Whenever you're ready to explore this in the future, feel free to keep my details handy. Wishing you and {hotel_name} continued success!

Best regards,
{from_name}"""

    elif intent == "contract_ready":
        subject = f"Website Development Agreement & Next Steps for {hotel_name}"
        body = f"""Hi {contact_name},

That is fantastic news! We are thrilled to partner with {hotel_name} to build your high-converting website, zero-commission direct booking engine, and customer reviews showcase.

To get started right away:
1. I have prepared your official **Website Development Agreement** attached below (outlining full scope, 7–10 day delivery timeline, and 50/50 milestone payment terms).
2. Once you review and confirm, we begin design immediately.
3. We will request your photos, room rates, and check-in policies to complete the build.

Please let me know if you would like any specific adjustments in the agreement, or if you are ready for me to send the digital signing link and invoice!

Best regards,
{from_name}"""
    else:
        subject = f"Re: {hotel_name} Website & Booking Engine"
        body = f"Hi {contact_name},\n\nThank you for your message regarding {hotel_name}. We look forward to helping you launch your direct booking and customer review engine.\n\nBest regards,\n{from_name}"

    return subject, body


def generate_contract(lead, price, currency="USD", cfg=None):
    if cfg is None:
        cfg = {}
    hotel_name = lead.get("hotel_name", "Client Hotel")
    contact_name = lead.get("contact_name", "Hotel Owner / General Manager")
    city = lead.get("city", "Hospitality Location")
    phone = lead.get("phone", "")
    email = lead.get("email", "")
    lead_id = lead.get("id", "LEAD-" + datetime.now().strftime("%Y%m%d"))
    contract_date = datetime.now().strftime("%B %d, %Y")
    agency_name = cfg.get("from_name", "Ahmad Raza Web Solutions")
    agency_email = cfg.get("smtp_user", "ahmadbkj92@gmail.com")

    # Payment calculations (50% deposit, 50% on completion)
    deposit = round(price * 0.5, 2)
    final_balance = round(price * 0.5, 2)

    contract = f"""# HOTEL WEBSITE & DIRECT BOOKING SYSTEM DEVELOPMENT AGREEMENT

**Agreement Reference:** HBD-{lead_id.upper()}-{datetime.now().strftime("%Y%m")}  
**Effective Date:** {contract_date}  

---

### PARTIES
This Web Development & Software Agreement ("Agreement") is entered into by and between:

1. **Service Provider / Developer:**  
   **{agency_name}**  
   Email: {agency_email}  
   (Hereinafter referred to as "Developer")

2. **Client / Property Owner:**  
   **{hotel_name}**  
   Attn: {contact_name}  
   Location: {city}  
   Email: {email} | Phone: {phone}  
   (Hereinafter referred to as "Client")

---

### 1. PROJECT SCOPE & DELIVERABLES
Developer agrees to design, build, and deploy a custom, modern hospitality website for Client equipped with the following turnkey modules:

#### A. Custom Mobile-First Website
- Modern, luxury design optimized for {hotel_name}
- High-resolution photo gallery & room walkthrough showcase
- Fast loading speed (under 1.5 seconds) with 100% mobile & tablet responsiveness
- Contact details, location map, amenities, and policy pages

#### B. Zero-Commission Direct Booking Engine
- Real-time room reservation engine with date picker, room selection, and instant confirmation
- Zero transaction commission to third-party OTAs (Client keeps 100% of room revenue)
- Secure payment gateway integration (Stripe / Razorpay / PayPal / Credit Cards / UPI)
- Automated email confirmation receipts to guests and notification alerts to management

#### C. Customer Reviews & Social Proof Engine
- Prominent customer review showcase widget on the homepage
- Integration of Google Reviews / TripAdvisor traveler ratings
- Verified customer feedback capture form to collect reviews from departing guests

#### D. Channel Manager & Availability Sync
- Two-way iCal / API calendar synchronization with Airbnb, Booking.com, and Agoda to prevent double-bookings
- Room rate and seasonal pricing configuration

---

### 2. TIMELINE & MILESTONES
- **Kickoff:** Within 24 hours of receiving initial deposit and property assets (photos/room descriptions).
- **Preview & Revision Review:** Day 5 to Day 7.
- **Final Deployment & Launch:** Completed within **7 to 10 business days** from kickoff.

---

### 3. TOTAL INVESTMENT & PAYMENT TERMS
- **Total Project Fee:** **{currency} {price:,.2f}**
- **Milestone 1 (Deposit):** **{currency} {deposit:,.2f}** (50%) due upon signing to initiate design & development.
- **Milestone 2 (Final Balance):** **{currency} {final_balance:,.2f}** (50%) due upon final approval and domain launch.

---

### 4. POST-LAUNCH WARRANTY & SUPPORT
- **30 Days Dedicated Support:** Includes free technical support, minor content tweaks, and staff training on managing bookings.
- **Full Ownership:** Upon receipt of final payment, Client owns 100% of website source code, design assets, and booking credentials.

---

### SIGNATURES & ACCEPTANCE

By signing below, the Parties agree to the terms, scope, and payment schedule set forth in this Agreement.

**DEVELOPER:**  
Signature: ___________________________  
Name: {agency_name}  
Date: {contract_date}  

**CLIENT / HOTEL OWNER:**  
Signature: ___________________________  
Name: {contact_name}  
Title: Authorized Signatory for {hotel_name}  
Date: ___________________________  
"""
    return contract


def main():
    p = argparse.ArgumentParser(description="Deal Closer & Contract Generator")
    sub = p.add_subparsers(dest="cmd", required=True)

    # Reply command
    sr = sub.add_parser("reply", help="Generate objection-handling response for a lead")
    sr.add_argument("--id", required=True, help="Lead ID")
    sr.add_argument("--intent", choices=["price", "ota_objection", "demo_interest", "no_need", "contract_ready"], help="Specific intent")
    sr.add_argument("--text", help="Client's incoming message text to auto-classify intent")

    # Contract command
    sc = sub.add_parser("contract", help="Generate web development contract for a lead")
    sc.add_argument("--id", required=True, help="Lead ID")
    sc.add_argument("--price", type=float, default=950.0, help="Total contract price")
    sc.add_argument("--currency", default="USD", help="Currency symbol/code (e.g. USD, INR, EUR)")
    sc.add_argument("--out", help="Save contract to file")

    args = p.parse_args()
    leads = load_leads()
    cfg = load_config()

    lead = next((l for l in leads if l.get("id") == args.id), None)
    if not lead:
        sys.exit(f"Lead not found with ID: {args.id}")

    if args.cmd == "reply":
        intent = args.intent
        if not intent and args.text:
            intent = detect_intent(args.text)
        elif not intent:
            intent = "price"

        subj, body = generate_cooperative_reply(lead, intent, cfg)
        print(f"=== CLASSIFIED INTENT: [{intent.upper()}] ===")
        print(f"SUBJECT: {subj}")
        print("-" * 50)
        print(body)

    elif args.cmd == "contract":
        contract_text = generate_contract(lead, args.price, args.currency, cfg)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(contract_text)
            print(f"Contract successfully generated and saved to {args.out}")
        else:
            print(contract_text)


if __name__ == "__main__":
    main()
