#!/usr/bin/env python3
"""Direct Google Sheets integration using gspread library."""
import json, csv, os, sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import gspread
    from google.oauth2.service_account import Credentials
    HAS_GSPREAD = True
except ImportError:
    HAS_GSPREAD = False

SHEET_ID = "1wt74LQbaVKT4um2Auv92lJDWF0lKj7_JejnrRBi26cY"
CSV_FILE = r"C:\Users\AHMAD RAJA\Desktop\hermes\indian_hotel_leads.csv"
SERVICE_ACCOUNT_FILE = os.path.join(
    r"C:\Users\AHMAD RAJA\Desktop\hermes\.agents\skills\hotel-website-outreach\data",
    "google-service-account.json"
)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def try_gspread_service_account():
    if not HAS_GSPREAD:
        return False, "gspread not installed"
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        return False, "No service_account.json at data/google-service-account.json"

    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.get_worksheet(0)

    if worksheet.row_count == 0:
        worksheet.append_row(["ID", "Hotel Name", "City", "Phone", "Email", "Website", "Status", "Date", "Audit Notes"])

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        leads = list(csv.DictReader(f))

    pushed = 0
    for row in leads:
        cell = worksheet.findall(row.get("hotel_name", "").strip())
        if not cell:
            worksheet.append_row([
                row.get("id", ""), row.get("hotel_name", ""), row.get("city", ""),
                row.get("phone", "") or "", row.get("email", "") or "",
                row.get("website", "") or "", row.get("status", "identified"),
                row.get("date_discovered", ""), row.get("audit_notes", "")
            ])
            pushed += 1

    return True, f"Pushed {pushed} of {len(leads)} leads"

def export_csv_for_manual_import():
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    out_file = r"C:\Users\AHMAD RAJA\Desktop\hermes\indian_hotel_leads_for_gsheet.csv"
    with open(out_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Hotel Name", "City", "Phone", "Email", "Website", "Status", "Date", "Audit Notes"])
        for r in rows:
            writer.writerow([
                r.get("id", ""), r.get("hotel_name", ""), r.get("city", ""),
                r.get("phone", "") or "", r.get("email", "") or "",
                r.get("website", "") or "", r.get("status", "identified"),
                r.get("date_discovered", ""), r.get("audit_notes", "")
            ])
    return out_file, len(rows)

# Try service account first
ok, msg = try_gspread_service_account()
if ok:
    print(f"[gsheets] SUCCESS: {msg}")
else:
    print(f"[gsheets] Auto-write unavailable: {msg}")
    print()
    out_file, count = export_csv_for_manual_import()
    print(f"[gsheets] Exported {count} leads to: {out_file}")
    print(f"[gsheets] Your Sheet ID: {SHEET_ID}")
    print()
    print("=== Option 1: Import CSV into Google Sheets ===")
    print("1. Open your Google Sheet")
    print("2. File -> Import -> Upload")
    print(f"3. Select: {out_file}")
    print("4. Choose: 'Replace current sheet' or 'Append to current sheet'")
    print("5. Separator: Comma -> Import Data")
    print()
    print("=== Option 2: Deploy Apps Script (automated) ===")
    print("1. Go to https://script.google.com")
    print("2. New Project -> paste: data/gsheets_webhook_template.gs")
    print(f"3. Sheet ID: {SHEET_ID} (already set)")
    print("4. Deploy -> New Deployment -> Web app")
    print("   Execute as: Me | Who has access: Anyone")
    print("5. Copy Web app URL -> paste into data/gsheets_config.json")
    print("6. Run: python indian_hotel_agent.py --sync-gsheet")
    print()
    print("=== Option 3: Service Account (programmatic) ===")
    print("1. Go to console.cloud.google.com -> IAM & Admin -> Service Accounts")
    print("2. Create service account -> Create key (JSON)")
    print("3. Save as: data/google-service-account.json")
    print(f"4. Share your Google Sheet with the service account email")
    print("5. Run: python indian_hotel_agent.py --sync-gsheet")
