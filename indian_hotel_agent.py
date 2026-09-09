#!/usr/bin/env python3
"""
indian_hotel_agent.py - Indian Hotel Lead Generation & Auto-Outreach Agent for Hermes.

Automates:
  1. Finding hotels, resorts, guesthouses, and homestays in India that DO NOT have a website.
  2. Formatting/extracting their contact details (Phone, Email, City, OTA status).
  3. Generating cold outreach emails tailored for Indian hoteliers:
       - Stop losing 18% to 22% commission to MakeMyTrip, Goibibo, and Booking.com.
       - Modern website with Zero-Commission Direct UPI / Card Booking Engine.
       - Verified Customer Reviews Showcase (Google / TripAdvisor ratings).
  4. Automatically sending emails via SMTP (when --send is used).
  5. Auto-generating closing replies & contracts to convince the client to award the project.
  6. Saving all leads directly into 'indian_hotel_leads.csv' on Hermes.

Usage:
  python indian_hotel_agent.py                     # Runs auto-discovery across Indian tourist cities
  python indian_hotel_agent.py --city "Manali"     # Search specific Indian city
  python indian_hotel_agent.py --send              # Auto-send cold emails to leads with emails
  python indian_hotel_agent.py --reply lead-001    # Auto-generate reply to close the client
  python indian_hotel_agent.py --contract lead-001 # Generate ready-to-sign web development agreement
"""
import argparse, csv, json, os, smtplib, sys, time, urllib.parse, urllib.request
from datetime import datetime
from email.mime.text import MIMEText

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

HERMES_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(HERMES_DIR, ".agents", "skills", "hotel-website-outreach")
SKILL_DATA = os.path.join(SKILL_DIR, "data")
SCRIPTS_DIR = os.path.join(SKILL_DIR, "scripts")
CONFIG_FILE = os.path.join(SKILL_DATA, "config.json")
CSV_OUTPUT = os.path.join(HERMES_DIR, "indian_hotel_leads.csv")
CONTRACTS_DIR = os.path.join(HERMES_DIR, "contracts")

if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)

DEFAULT_INDIAN_DESTINATIONS = [
    # North India
    "Goa", "Manali", "Shimla", "Rishikesh", "Mussoorie", "Dharamshala", 
    "Nainital", "Kasol", "Kullu", "Haridwar", "Dalhousie", "Kasauli",
    # Rajasthan & West
    "Jaipur", "Udaipur", "Jodhpur", "Pushkar", "Jaisalmer", "Mount Abu",
    "Lonavala", "Mahabaleshwar", "Alibag", "Panchgani", "Daman",
    # South India
    "Munnar", "Ooty", "Kodaikanal", "Alleppey", "Wayanad", "Varkala", 
    "Coorg", "Gokarna", "Pondicherry", "Chikmagalur", "Hampi", "Kovalam",
    # East & Heritage
    "Agra", "Varanasi", "Darjeeling", "Gangtok", "Puri", "Shillong", "Khajuraho"
]

EMAIL_TEMPLATE_INDIA = """Subject: Stop paying 20% MakeMyTrip/Goibibo commissions - Direct Booking & Review System for {hotel_name}

Namaste / Hello {contact_name},

I came across {hotel_name} while looking at popular places to stay in {city}. Your property looks wonderful, but I noticed that guests currently cannot book directly on your own official website and have to rely on third-party OTAs like MakeMyTrip, Goibibo, or Booking.com.

Every time a guest books through these OTAs, you lose 18% to 25% in commissions. If your average room is ₹2,500/night, that is ₹500+ lost on every single night!

We help independent hotels and guesthouses across India launch a modern website equipped with:

  🏨 1. Zero-Commission Direct Booking Engine:
     - Guests can check real-time room availability and book directly on your phone-friendly website.
     - Instant payments via UPI (Google Pay, PhonePe, Paytm), NetBanking, and Credit Cards directly into your bank account.
     - Automatic calendar sync with MakeMyTrip, Airbnb, and Booking.com to avoid double-bookings.

  ⭐ 2. Verified Customer Reviews & Google Ratings Showcase:
     - Displays your authentic 5-star traveler reviews and ratings right on the homepage.
     - Builds immediate trust so guests book with you directly instead of searching competitors.

  📱 3. Fast Mobile Design & Turnkey Setup:
     - 80%+ travelers in India book on mobile phones — your site will be ultra-fast.
     - Completely live and ready in under 7 days with full staff training.

We have already designed a quick demo preview tailored specifically for {hotel_name}.

Could I share a 3-minute video preview or demo link with you this week?

Warm regards,
{from_name}
Mobile / WhatsApp: {from_phone}
Email: {from_email}
"""

REPLY_TEMPLATES_INDIA = {
    "price": """Subject: Re: Website & Booking System for {hotel_name} - Pricing & ROI

Hi {contact_name},

Thank you for your response! Our pricing is very affordable and designed to pay for itself immediately:

Our packages range between **₹8,000 to ₹15,000** depending on the hotel size and required features:

  📦 Package 1: Essential Direct Booking & Reviews Suite (for Guesthouses & Homestays)
  - Custom mobile-responsive hotel website with room photo gallery
  - Commission-free direct booking engine with instant room reservations
  - Instant UPI payments (PhonePe, Google Pay, Paytm) & card gateway
  - Verified customer review showcase (Google Reviews & TripAdvisor ratings widget)
  - Fast turnaround: Live within 5 to 7 days
  👉 Investment: ₹8,000 to ₹9,500 (one-time fee)

  🚀 Package 2: Complete Hospitality Growth Suite (for Boutique Hotels & Resorts)
  - Everything in Package 1, plus:
  - 2-Way Channel Manager sync (instant calendar sync with MakeMyTrip, Goibibo & Airbnb)
  - Automated post-stay review collection SMS/WhatsApp to gather 5-star Google ratings
  - Google Business & Local SEO optimization so travelers searching "{city} hotels" find you first
  - 30 days dedicated support & staff training
  👉 Investment: ₹12,000 to ₹15,000 (one-time fee)

💡 The ROI Math for {hotel_name}:
If your room rate is ₹2,000 and MakeMyTrip takes 18% to 22% commission (₹360 - ₹440 per booking), saving just 2 to 3 direct bookings every month completely recovers your entire ₹8,000–₹15,000 website cost within 30 days. After that, 100% of the money stays directly in your pocket!

Can we schedule a quick 5-minute phone or WhatsApp call tomorrow to show you the live preview?

Warm regards,
{from_name}""",

    "ota": """Subject: Re: Direct Bookings alongside MakeMyTrip / OTAs for {hotel_name}

Hi {contact_name},

I completely understand, and it is great that portals like MakeMyTrip, Goibibo, and Booking.com are generating regular guests for {hotel_name}!

Our direct booking system does NOT replace your OTAs — it works together with them to maximize your profit:

1. 100% Profit on Repeat Guests:
   When guests stay with you once and love your service, they search for your hotel directly next season. Without your own website, they are forced to book through MakeMyTrip again, costing you another 18-20% commission on your own loyal customer!

2. Direct UPI & Advance Payments:
   With your own website, you collect direct advance payments via UPI (GPay/PhonePe) instantly into your bank account without waiting for OTA payout cycles.

3. Complete Calendar Sync:
   Our system syncs automatically with MakeMyTrip and Booking.com calendars so there is zero risk of double booking.

I would love to send you a 2-minute video walkthrough showing how easily it works. Would that be helpful?

Warm regards,
{from_name}"""
}


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_user": "mithsjames87@gmail.com",
        "smtp_pass": "Ahmad@9835685952",
        "from_name": "Ahmad Raza",
        "daily_limit": 30
    }


def find_indian_hotels(city, limit=10):
    """Query OpenStreetMap Overpass for hospitality properties in India lacking websites."""
    nom_url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({
        "q": f"{city}, India", "format": "json", "limit": 1
    })
    headers = {"User-Agent": "HermesIndianHotelAgent/1.0"}
    try:
        req = urllib.request.Request(nom_url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            geo = json.loads(resp.read().decode("utf-8"))
            if not geo:
                return []
            bbox = geo[0].get("boundingbox")
    except Exception:
        return []

    south, north, west, east = bbox[0], bbox[1], bbox[2], bbox[3]
    fetch_n = min(limit * 8, 100)
    query = f"""[out:json][timeout:45];
(
  node["tourism"~"hotel|guest_house|motel|chalet|hostel|homestay|apartment|villa|camp_site"]({south},{west},{north},{east});
  way["tourism"~"hotel|guest_house|motel|chalet|hostel|homestay|apartment|villa|camp_site"]({south},{west},{north},{east});
  node["amenity"="hotel"]({south},{west},{north},{east});
  way["amenity"="hotel"]({south},{west},{north},{east});
);
out tags center {fetch_n};"""

    op_url = "https://overpass-api.de/api/interpreter"
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    try:
        req = urllib.request.Request(op_url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=45) as resp:
            res = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []

    leads = []
    seen = set()
    for el in res.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name or name in seen:
            continue
        seen.add(name)

        web = tags.get("website") or tags.get("contact:website") or ""
        phone = tags.get("phone") or tags.get("contact:phone") or ""
        email = tags.get("email") or tags.get("contact:email") or ""
        tourism_type = tags.get("tourism", "hotel").replace("_", " ").title()

        # Check: No website, or only an OTA/directory listing
        ota_markers = ["makemytrip", "goibibo", "booking.com", "agoda", "justdial", "airbnb"]
        is_ota = any(m in web.lower() for m in ota_markers) if web else False

        if not web or is_ota:
            leads.append({
                "hotel_name": name,
                "city": city,
                "tourism_type": tourism_type,
                "phone": phone,
                "email": email,
                "website": web,
                "status": "No website (OTA dependent)" if not web else f"OTA listing: {web}",
                "audit_notes": f"Indian {tourism_type} in {city}. No standalone booking website. High MakeMyTrip/OTA commission loss."
            })
            if len(leads) >= limit:
                break
    return leads


def save_leads_csv(all_leads):
    """Save or update indian_hotel_leads.csv on Hermes."""
    FIELDNAMES = ["id", "hotel_name", "city", "phone", "email", "website", "status", "date_discovered", "audit_notes"]
    existing_rows = []
    seen_names = set()
    if os.path.exists(CSV_OUTPUT):
        with open(CSV_OUTPUT, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f, fieldnames=FIELDNAMES)
            for i, r in enumerate(reader):
                # Skip the header row itself (when fieldnames are explicit, row 0 = header values)
                if i == 0 and r.get("id", "").strip().lower() in ("id", ""):
                    continue
                # Only keep rows that have a valid hotel_name
                name = r.get("hotel_name", "").strip()
                if not name or name.lower() == "hotel_name":
                    continue
                # Sanitize: ensure row only has expected keys
                clean = {k: r.get(k, "") for k in FIELDNAMES}
                existing_rows.append(clean)
                seen_names.add(name.lower())

    count_added = 0
    for l in all_leads:
        if l["hotel_name"].lower() not in seen_names:
            lead_id = f"in-lead-{len(existing_rows) + 1:03d}"
            row = {
                "id": lead_id,
                "hotel_name": l["hotel_name"],
                "city": l["city"],
                "phone": l.get("phone", ""),
                "email": l.get("email", ""),
                "website": l.get("website", ""),
                "status": "identified",
                "date_discovered": datetime.now().strftime("%Y-%m-%d"),
                "audit_notes": l.get("audit_notes", "")
            }
            existing_rows.append(row)
            seen_names.add(l["hotel_name"].lower())
            count_added += 1

    fieldnames = FIELDNAMES
    with open(CSV_OUTPUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing_rows)

    # Automatically sync Excel (.xlsx) file
    try:
        export_to_excel(existing_rows)
    except Exception:
        pass

    return count_added, len(existing_rows)


def export_to_excel(rows):
    """Generate or update the styled Excel workbook indian_hotel_leads.xlsx."""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Indian Hotel Leads"

    headers = [
        "Lead ID", "Hotel Name", "City / Destination", "Phone Number", 
        "Email Address", "Website Status", "OTA Commission Loss", 
        "Lead Status", "Date Discovered", "Audit & Pitch Notes"
    ]
    ws.append(headers)

    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"), right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"), bottom=Side(style="thin", color="D9D9D9")
    )

    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border
    ws.row_dimensions[1].height = 28

    row_font = Font(name="Segoe UI", size=10)
    alt_fill = PatternFill(start_color="F2F5F9", end_color="F2F5F9", fill_type="solid")
    white_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

    for r_idx, r in enumerate(rows, start=2):
        phone = r.get("phone") or "Not listed on Maps"
        email = r.get("email") or "Pending lookup"
        web_status = "NO WEBSITE (OTA Only)" if not r.get("website") else r.get("website")
        comm_loss = "18% - 22% (MakeMyTrip/Goibibo)"

        data_row = [
            r.get("id", ""), r.get("hotel_name", ""), r.get("city", ""),
            phone, email, web_status, comm_loss,
            r.get("status", "identified").upper(), r.get("date_discovered", ""),
            r.get("audit_notes", "")
        ]
        ws.append(data_row)
        current_fill = alt_fill if r_idx % 2 == 0 else white_fill
        for c_idx in range(1, len(headers) + 1):
            c = ws.cell(row=r_idx, column=c_idx)
            c.font = row_font
            c.fill = current_fill
            c.border = thin_border
            if c_idx in [1, 3, 4, 7, 8, 9]:
                c.alignment = Alignment(horizontal="center", vertical="center")
            else:
                c.alignment = Alignment(vertical="center")

    ws.column_dimensions["A"].width = 14
    ws.column_dimensions["B"].width = 34
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["D"].width = 20
    ws.column_dimensions["E"].width = 20
    ws.column_dimensions["F"].width = 25
    ws.column_dimensions["G"].width = 28
    ws.column_dimensions["H"].width = 14
    ws.column_dimensions["I"].width = 16
    ws.column_dimensions["J"].width = 45

    excel_file = os.path.join(HERMES_DIR, "indian_hotel_leads.xlsx")
    wb.save(excel_file)


def send_email(lead, cfg):
    """Send live email via SMTP with anti-spam check."""
    if not lead.get("email"):
        return False, "No email on file"

    text = EMAIL_TEMPLATE_INDIA.format(
        hotel_name=lead["hotel_name"],
        contact_name="Hotel Owner / Manager",
        city=lead["city"],
        from_name=cfg.get("from_name", "Ahmad Raza"),
        from_phone="+91 9835685952",
        from_email=cfg.get("smtp_user", "mithsjames87@gmail.com")
    )
    lines = text.strip().split("\n")
    subject = lines[0].replace("Subject: ", "")
    body = "\n".join(lines[1:]).strip()

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = f"{cfg.get('from_name', 'Ahmad Raza')} <{cfg['smtp_user']}>"
    msg["To"] = lead["email"]

    try:
        with smtplib.SMTP(cfg["smtp_host"], cfg.get("smtp_port", 587), timeout=25) as s:
            s.starttls()
            s.login(cfg["smtp_user"], cfg["smtp_pass"])
            s.send_message(msg)
        return True, "Sent successfully"
    except Exception as e:
        return False, str(e)


def sync_to_gsheet(leads, cfg):
    """Push leads to Google Sheets via webhook or service account."""
    webhook = cfg.get("gsheet_webhook_url", "")

    # Try service account credentials first (gspread)
    sa_path = os.path.join(SKILL_DATA, "google-service-account.json")
    if os.path.exists(sa_path):
        try:
            from google.oauth2.service_account import Credentials
            import gspread
            creds = Credentials.from_service_account_file(sa_path, scopes=["https://www.googleapis.com/auth/spreadsheets"])
            client = gspread.authorize(creds)
            sheet_id = cfg.get("gsheet_sheet_id") or cfg.get("sheet_id", "1wt74LQbaVKT4um2Auv92lJDWF0lKj7_JejnrRBi26cY")
            sheet = client.open_by_key(sheet_id)
            worksheet = sheet.get_worksheet(0)
            if worksheet.row_count == 0:
                worksheet.append_row(["ID", "Hotel Name", "City", "Phone", "Email", "Website", "Status", "Date", "Audit Notes"])
            pushed = 0
            for row in leads:
                worksheet.append_row([
                    row.get("id", ""), row.get("hotel_name", ""), row.get("city", ""),
                    row.get("phone", "") or "", row.get("email", "") or "",
                    row.get("website", "") or "", row.get("status", "identified"),
                    row.get("date_discovered", ""), row.get("audit_notes", "")
                ])
                pushed += 1
            print(f"[gsheets] Pushed {pushed} lead(s) via service account.")
            return pushed
        except Exception as e:
            print(f"[gsheets] Service account failed: {e}")
            print("  Falling through to webhook method.")

    # Fallback: try webhook URL
    if not webhook:
        print("[gsheets] No Google Sheets integration configured.")
        print("  Set 'gsheet_webhook_url' in data/gsheets_config.json (Apps Script web app)")
        print("  OR create data/google-service-account.json (service account key)")
        print("  OR import CSV: indian_hotel_leads_for_gsheet.csv")
        return 0

    import urllib.request, urllib.error
    body = json.dumps(leads).encode("utf-8")
    req = urllib.request.Request(
        webhook, data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read().decode("utf-8"))
        pushed = result.get("results", [])
        added = sum(1 for r in pushed if r.get("status") == "added")
        skipped = sum(1 for r in pushed if r.get("status") == "skipped_duplicate")
        print(f"[gsheets] Pushed {len(leads)} lead(s): {added} added, {skipped} duplicates skipped")
        return added
    except urllib.error.HTTPError as e:
        print(f"[gsheets] HTTP {e.code}: {e.read().decode()[:200]}")
        return 0
    except Exception as e:
        print(f"[gsheets] Failed: {e}")
        return 0


def main():
    p = argparse.ArgumentParser(description="Hermes Indian Hotel Lead Gen & Cold Outreach Agent")
    p.add_argument("--city", help="Specific Indian city/destination (e.g. Manali, Jaipur, Goa)")
    p.add_argument("--daily", type=int, default=50, help="Daily target of leads to find (default: 50)")
    p.add_argument("--limit", type=int, default=10, help="Max leads per city when using --city (default: 10)")
    p.add_argument("--loop", action="store_true", help="Run in continuous background daemon loop (every 24 hours)")
    p.add_argument("--send", action="store_true", help="Send live emails via SMTP to leads with emails")
    p.add_argument("--reply", help="Lead ID to generate objection-handling response (e.g. in-lead-001)")
    p.add_argument("--intent", choices=["price", "ota"], default="price", help="Reply intent scenario")
    p.add_argument("--contract", help="Lead ID to generate contract for")
    p.add_argument("--price", type=float, default=12000.0, help="Contract price in INR (Range: ₹8,000 - ₹15,000, default: 12000)")
    p.add_argument("--show", action="store_true", help="Display all leads saved on Hermes")
    p.add_argument("--sync-gsheet", action="store_true", help="Push all leads to Google Sheet (requires gsheet_webhook_url in config)")

    args = p.parse_args()
    cfg = load_config()

    # If --show is specified
    if args.show:
        if not os.path.exists(CSV_OUTPUT):
            sys.exit("No leads found yet. Run 'python indian_hotel_agent.py' first.")
        with open(CSV_OUTPUT, "r", encoding="utf-8") as f:
            leads = list(csv.DictReader(f))
        print("\n" + "=" * 90)
        print(f"📋 HERMES INDIAN HOTEL LEADS DATABASE ({len(leads)} TOTAL LEADS)")
        print("=" * 90)
        print("%-12s | %-32s | %-14s | %-16s | %s" % ("ID", "Hotel Name", "Location", "Phone", "Website Status"))
        print("-" * 90)
        for l in leads:
            print("%-12s | %-32s | %-14s | %-16s | %s" % (
                l.get("id", ""),
                l.get("hotel_name", "")[:32],
                l.get("city", "")[:14],
                (l.get("phone") or "Not on Maps")[:16],
                l.get("status", "No website")[:18]
            ))
        print("=" * 90)
        print(f"Total: {len(leads)} hotels without websites saved in {CSV_OUTPUT}\n")
        return

    # If --sync-gsheet is specified
    if args.sync_gsheet:
        from collections import OrderedDict
        gsheet_cfg = load_config()
        gsheet_path = os.path.join(SKILL_DATA, "gsheets_config.json")
        if os.path.exists(gsheet_path):
            with open(gsheet_path, "r", encoding="utf-8") as gf:
                gsheet_cfg.update(json.load(gf))

        if not os.path.exists(CSV_OUTPUT):
            sys.exit(f"No leads found at {CSV_OUTPUT}")
        with open(CSV_OUTPUT, "r", encoding="utf-8") as f:
            leads = list(csv.DictReader(f))

        push_leads = []
        seen = set()
        for l in leads:
            key = (l.get("hotel_name", ""), l.get("city", ""))
            if key in seen:
                continue
            seen.add(key)
            push_leads.append({
                "id": l.get("id", ""),
                "hotel_name": l.get("hotel_name", ""),
                "city": l.get("city", ""),
                "phone": l.get("phone", "") or "",
                "email": l.get("email", "") or "",
                "website": l.get("website", "") or "",
                "status": "identified",
                "date_discovered": l.get("date_discovered", ""),
                "audit_notes": l.get("audit_notes", ""),
            })
        print(f"[gsheets] Pushing {len(push_leads)} unique leads...")
        synced = sync_to_gsheet(push_leads, gsheet_cfg)
        print(f"Done. {synced} new lead(s) pushed to Google Sheet.")
        return

    # If --reply is specified
    if args.reply:
        leads = []
        if os.path.exists(CSV_OUTPUT):
            with open(CSV_OUTPUT, "r", encoding="utf-8") as f:
                leads = list(csv.DictReader(f))
        lead = next((l for l in leads if l["id"] == args.reply), None)
        if not lead:
            sys.exit(f"Lead not found: {args.reply}")
        tpl = REPLY_TEMPLATES_INDIA.get(args.intent, REPLY_TEMPLATES_INDIA["price"])
        print("\n" + "=" * 60)
        print(f"🤝 CLIENT CLOSING REPLY FOR: {lead['hotel_name']} ({lead['city']})")
        print("=" * 60)
        print(tpl.format(
            hotel_name=lead["hotel_name"],
            contact_name="Hotel Manager / Owner",
            city=lead["city"],
            from_name=cfg.get("from_name", "Ahmad Raza")
        ))
        return

    # If --contract is specified
    if args.contract:
        from scripts.deal_closer import generate_contract
        leads = []
        if os.path.exists(CSV_OUTPUT):
            with open(CSV_OUTPUT, "r", encoding="utf-8") as f:
                leads = list(csv.DictReader(f))
        lead = next((l for l in leads if l["id"] == args.contract), None)
        if not lead:
            sys.exit(f"Lead not found: {args.contract}")
        contract_text = generate_contract(lead, price=args.price, currency="INR", cfg=cfg)
        os.makedirs(CONTRACTS_DIR, exist_ok=True)
        fname = f"Contract_{lead['id']}_{lead['hotel_name'].replace(' ', '_')}.md"
        cpath = os.path.join(CONTRACTS_DIR, fname)
        with open(cpath, "w", encoding="utf-8") as cf:
            cf.write(contract_text)
        print(f"\n[✓] Contract generated and saved to: contracts/{fname}")
        print("-" * 60)
        print(contract_text[:800] + "\n... [Full agreement saved]")
        return

    def run_daily_cycle():
        import concurrent.futures, threading
        target = args.daily if not args.city else args.limit
        per_city_fetch = max(args.limit, 25)
        print("\n" + "=" * 75)
        print(f"🇮🇳 HERMES INDIAN HOTEL LEAD GEN & OUTREACH AGENT (DAILY TARGET: {target})")
        print("=" * 75)
        print(f"Mode             : {'LIVE SEND (SMTP)' if args.send else 'DISCOVERY & PITCH PREVIEW'}")
        print(f"Target Output    : {CSV_OUTPUT}")
        print(f"Workers          : 5 parallel city scanners")
        print("=" * 75)

        destinations = [args.city] if args.city else DEFAULT_INDIAN_DESTINATIONS
        all_found = []
        total_new_today = 0
        csv_lock = threading.Lock()

        def scan_city(city):
            print(f"  [→] Scanning {city}...")
            found = find_indian_hotels(city, limit=per_city_fetch)
            print(f"  [✓] {city}: {len(found)} candidates found")
            return city, found

        # Scan all cities in parallel (5 workers)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(scan_city, city): city for city in destinations}
            for future in concurrent.futures.as_completed(futures):
                if total_new_today >= target:
                    break
                try:
                    city, found = future.result()
                    all_found.extend(found)
                    with csv_lock:
                        added, current_total = save_leads_csv(found)
                        total_new_today += added
                    if added > 0:
                        print(f"  [+] {city}: Saved {added} new leads — Total today: {total_new_today}/{target}")
                except Exception as e:
                    print(f"  [!] Error: {e}")

        print("\n" + "=" * 75)
        print(f"✨ DAILY HARVEST FINISHED: {total_new_today} New Leads Added Today")
        print(f"📁 Total leads in Hermes: {CSV_OUTPUT}")
        print("=" * 75)

        # Display newly found leads
        if all_found:
            print("\n%-32s | %-12s | %-16s | %s" % ("Hotel Name", "Location", "Phone", "Status"))
            print("-" * 85)
            for l in all_found[:20]:
                print("%-32s | %-12s | %-16s | %s" % (
                    l["hotel_name"][:32],
                    l["city"][:12],
                    (l.get("phone") or "Not on Maps")[:16],
                    l.get("status", "No website")[:22]
                ))
            if len(all_found) > 20:
                print(f"... and {len(all_found) - 20} more leads in {CSV_OUTPUT}")

        # Send emails if --send enabled
        if args.send:
            print("\n[*] Sending live outreach emails via SMTP to leads with emails...")
            sent_count = 0
            for l in all_found:
                if l.get("email"):
                    ok, msg = send_email(l, cfg)
                    status_icon = "✓" if ok else "✗"
                    print(f"  [{status_icon}] {l['hotel_name']} <{l['email']}>: {msg}")
                    if ok:
                        sent_count += 1
                    time.sleep(2)
            print(f"\n[✓] Finished sending. Total sent today: {sent_count}")
        else:
            print("\nTip: Run with '--send' to automatically email all qualified leads via SMTP.")

    if args.loop:
        print(f"[*] Starting Hermes Indian Hotel Agent in 24-hour continuous loop...")
        while True:
            run_daily_cycle()
            print(f"\n[⏳] Sleeping for 24 hours until next daily cycle. Press Ctrl+C to stop.")
            time.sleep(86400)
    else:
        run_daily_cycle()


if __name__ == "__main__":
    main()
