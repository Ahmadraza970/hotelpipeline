#!/usr/bin/env python3
"""
daily_auto_pipeline.py - Full auto hotel pipeline for Hermes
Runs: find Pune+Goa -> Serper enrich -> strict MX verify -> push to Google Sheet -> Gmail send (verified only) -> wait
Called automatically at Windows logon and daily 9am via Task Scheduler, no manual reply needed.
"""
import csv, json, os, re, time, base64, subprocess, sys, tempfile
from email.mime.text import MIMEText
from datetime import datetime

HERMES_DIR = os.environ.get("HERMES_DIR", r"C:\Users\AHMAD RAJA\Desktop\hermes")
# when run via hermes cron workdir, __file__ is in scripts folder; always use project dir
if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "indian_hotel_leads.csv")):
    HERMES_DIR = os.path.dirname(os.path.abspath(__file__))
# force project dir if running from scripts
if not os.path.exists(os.path.join(HERMES_DIR, "indian_hotel_leads.csv")):
    HERMES_DIR = os.environ.get("HERMES_DIR", r"C:\Users\AHMAD RAJA\Desktop\hermes")
# GitHub Actions: allow override via env
if os.environ.get("GITHUB_ACTIONS") == "true":
    HERMES_DIR = os.getcwd()
CSV = os.path.join(HERMES_DIR, "indian_hotel_leads.csv")
SHEET_ID = os.environ.get("SHEET_ID", "1wt74LQbaVKT4um2Auv92lJDWF0lKj7_JejnrRBi26cY")
SENT_LOG = os.path.join(HERMES_DIR, "sent_log_goa_pune.json")
SERPER_KEY = os.environ.get("SERPER_KEY", "d0f391c08934a027ae79ef736de987af6a16de36")
GOOGLE_TOKEN = os.environ.get("GOOGLE_TOKEN", "C:/Users/AHMAD RAJA/AppData/Local/hermes/google_token.json")

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def find_leads():
    log("Step 1: Finding leads Pune+Goa via indian_hotel_agent")
    import subprocess as sp
    for city, limit in [("Pune", 25), ("Goa", 10)]:
        sp.run([sys.executable, os.path.join(HERMES_DIR, "indian_hotel_agent.py"), "--city", city, "--limit", str(limit)], timeout=120)

def serper_enrich():
    log("Step 2: Serper enrich for leads without email")
    import urllib.request, json as js
    rows=list(csv.DictReader(open(CSV, encoding='utf-8')))
    targets=[r for r in rows if not r['email'].strip()][:20]  # enrich 20 per run to stay within credits
    if not targets:
        log("No leads need enriching")
        return
    def s_search(q):
        d=js.dumps({'q':q,'num':5}).encode()
        req=urllib.request.Request('https://google.serper.dev/search', data=d, headers={'X-API-KEY':SERPER_KEY,'Content-Type':'application/json'})
        with urllib.request.urlopen(req, timeout=15) as r:
            return js.loads(r.read().decode())
    def ext_email(t):
        ms=re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', t)
        filt=[e for e in ms if 'info@gmail.com' not in e.lower() and 'example' not in e.lower()]
        pref=[e for e in filt if any(k in e.lower() for k in ['contact','info','reservation','booking','sales'])]
        return (pref[0] if pref else (filt[0] if filt else ''))
    def ext_phone(t):
        ms=re.findall(r'\+91[\s\-]*\d{10}|\b0?\d{10}\b', t)
        return ms[0] if ms else ''
    updated=0
    for lead in targets:
        q=f"{lead['hotel_name']} {lead['city']} contact email phone"
        try:
            res=s_search(q)
            blob=' '.join([(o.get('snippet','')+' '+o.get('link','')) for o in res.get('organic',[])])
            email=ext_email(blob)
            phone=ext_phone(blob)
            if email:
                lead['email']=email; updated+=1
            if phone and not lead['phone'].strip():
                lead['phone']=phone
            log(f"Enriched {lead['hotel_name']} -> {email or '-'}")
        except Exception as e:
            log(f"Enrich err {lead['hotel_name']} {e}")
        time.sleep(1.2)
    # write back
    id_map={r['id']:r for r in targets}
    for r in rows:
        if r['id'] in id_map:
            r['email']=id_map[r['id']]['email']
            r['phone']=id_map[r['id']]['phone']
    FIELDNAMES=['id','hotel_name','city','phone','email','website','status','date_discovered','audit_notes']
    rows.sort(key=lambda x: x['id'])
    with open(CSV,'w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows([{k:r.get(k,'') for k in FIELDNAMES} for r in rows])
    log(f"Enriched {updated}/{len(targets)}")

def strict_verify_and_clean():
    log("Step 2b: Strict verify (MX via 8.8.8.8, drop bad domains)")
    import subprocess as sp
    rows=list(csv.DictReader(open(CSV, encoding='utf-8')))
    def mx_ok(domain):
        try:
            out=sp.run(['nslookup','-type=mx',domain,'8.8.8.8'], capture_output=True, text=True, timeout=10)
            if 'mail exchanger' in out.stdout.lower():
                return True
            if 'non-existent domain' in out.stdout.lower() or "can't find" in out.stdout.lower():
                return False
            out2=sp.run(['nslookup',domain,'8.8.8.8'], capture_output=True, text=True, timeout=10)
            if 'address' in out2.stdout.lower() and 'non-existent' not in out2.stdout.lower():
                return False  # A only, no MX -> treat as bad for strict
            return False
        except:
            return False
    cleaned=0
    for r in rows:
        if r['email'].strip():
            domain=r['email'].split('@')[-1]
            if domain.lower() in ['hotelgreenparkgoa.com','gtdchotel.com'] or r['email'].lower()=='info@gmail.com' or 'commonfloor.com' in domain.lower():
                log(f"Cleaning {r['id']} {r['email']} (known bad)")
                r['email']=''
                cleaned+=1
            elif not mx_ok(domain):
                log(f"Cleaning {r['id']} {r['email']} (no MX)")
                r['email']=''
                cleaned+=1
    FIELDNAMES=['id','hotel_name','city','phone','email','website','status','date_discovered','audit_notes']
    rows.sort(key=lambda x: x['id'])
    with open(CSV,'w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows([{k:r.get(k,'') for k in FIELDNAMES} for r in rows])
    log(f"Strict cleaned {cleaned}, now {len([r for r in rows if r['email'].strip()])}/{len(rows)} with email")

def sync_csv():
    """Write enriched emails + sent status back to CSV so commits reflect actual state."""
    log("Step 2c: Syncing enriched emails + sent status to CSV")
    rows = list(csv.DictReader(open(CSV, encoding='utf-8')))
    try:
        sent_data = json.load(open(SENT_LOG, encoding='utf-8'))
        sent_ids = {s['id'] for s in sent_data['sent']}
        # Build lookup: id -> email from sent_log
        sent_email_map = {s['id']: s['email'] for s in sent_data['sent']}
    except:
        sent_ids = set()
        sent_email_map = {}
    emails_before = sum(1 for r in rows if r.get('email', '').strip())
    for row in rows:
        if row['id'] in sent_ids:
            row['status'] = 'sent'
            # Copy email from sent_log so CSV reflects what was actually sent
            if row['id'] in sent_email_map:
                row['email'] = sent_email_map[row['id']]
    FIELDNAMES = list(rows[0].keys())
    rows.sort(key=lambda x: x['id'])
    with open(CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(rows)
    emails_after = sum(1 for r in rows if r.get('email', '').strip())
    log(f"CSV synced: {len(rows)} rows, emails: {emails_before}→{emails_after}, sent marked: {len(sent_ids)}")

def push_to_sheet():
    log(f"Step 3: Pushing to Google Sheet {SHEET_ID} via Sheets API")
    rows=list(csv.DictReader(open(CSV, encoding='utf-8')))
    vals=[['Lead ID','Hotel Name','City / Destination','Phone Number','Email Address','Website Status','OTA Commission Loss','Lead Status','Date Discovered','Audit & Pitch Notes']]
    for r in rows:
        vals.append([r.get('id',''), r.get('hotel_name',''), r.get('city',''), r.get('phone') or 'Not listed', r.get('email') or 'Pending lookup', 'NO WEBSITE (OTA Only)' if not r.get('website') else 'HAS WEBSITE', 'Yes', 'Pending', r.get('date_discovered',''), r.get('audit_notes','')])
    import json as js
    import subprocess as sp
    
    # Use cross-platform temp file instead of hardcoded Windows path
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        tmp = f.name
        js.dump(vals, f)
    
    try:
        res=sp.run([sys.executable, "C:/Users/AHMAD RAJA/AppData/Local/hermes/skills/productivity/google-workspace/scripts/google_api.py", "sheets", "update", SHEET_ID, "Sheet1!A1", "--values", tmp], capture_output=True, text=True)
        if res.returncode==0:
            log(f"Pushed {len(vals)-1} leads to sheet: {res.stdout[:100]}")
        else:
            log(f"Sheet push failed: {res.stderr[:300]}")
    finally:
        # Clean up temp file
        if os.path.exists(tmp):
            os.remove(tmp)

def send_verified():
    log("Step 4: Sending via Gmail API to verified unsent leads (max 20/day)")
    rows=list(csv.DictReader(open(CSV, encoding='utf-8')))
    try:
        sent=json.load(open(SENT_LOG,encoding='utf-8'))
        sent_ids=set([s['id'] for s in sent['sent']])
    except:
        sent={'sent':[]}; sent_ids=set()
    # verified = with email and not yet sent, and not in drop list, and city Pune/Goa first
    candidates=[r for r in rows if r['email'].strip() and r['id'] not in sent_ids]
    # prioritize Goa/Pune, then others
    candidates.sort(key=lambda x: (0 if x['city'].lower() in ('goa','pune') else 1, x['id']))
    batch=candidates[:20]  # daily limit
    if not batch:
        log("No verified unsent leads to send, waiting for reply")
        return
    log(f"Sending batch {len(batch)}: {[r['id'] for r in batch]}")
    template='''Namaste / Hello Hotel Owner / Manager,

I came across {hotel_name} while looking at popular places to stay in {city}. Your property looks wonderful, but I noticed that guests currently cannot book directly on your own official website.

Every time a guest books through these OTAs, you lose 18% to 25% in commissions. If your average room is Rs.2,500/night, that is Rs.500+ lost on every single night!

We help independent hotels and guesthouses across India launch a modern website equipped with:

  1. Zero-Commission Direct Booking Engine:
     - Guests can check real-time room availability and book directly on your phone-friendly website.
     - Instant payments via UPI (Google Pay, PhonePe, Paytm), NetBanking, and Credit Cards directly into your bank account.
     - Automatic calendar sync with MakeMyTrip, Airbnb, and Booking.com to avoid double-bookings.

  2. Verified Customer Reviews & Google Ratings Showcase:
     - Displays your authentic 5-star traveler reviews and ratings right on the homepage.
     - Builds immediate trust so guests book with you directly instead of searching competitors.

  3. Fast Mobile Design & Turnkey Setup:
     - 80%+ travelers in India book on mobile phones — your site will be ultra-fast.
     - Completely live and ready in under 7 days with full staff training.

We have already designed a quick demo preview tailored specifically for {hotel_name}.

Could I share a 3-minute video preview or demo link with you this week?

Warm regards,
Ahmad Raza
Mobile / WhatsApp: +91 9835685952
Email: ahmadbkj92@gmail.com

P.S. If you prefer not to receive these updates, reply with "Unsubscribe" and I will remove you immediately.
'''
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds=Credentials.from_authorized_user_file(GOOGLE_TOKEN, ['https://www.googleapis.com/auth/gmail.send'])
    service=build('gmail','v1', credentials=creds)
    sent_now=[]
    for lead in batch:
        subject=f"Stop paying 20% MakeMyTrip/Goibibo commissions - Direct Booking & Review System for {lead['hotel_name']}"
        body=template.format(hotel_name=lead['hotel_name'], city=lead['city'])
        msg=MIMEText(body,'plain','utf-8')
        msg['To']=lead['email']
        msg['From']='Ahmad Raza <ahmadbkj92@gmail.com>'
        msg['Subject']=subject
        raw=base64.urlsafe_b64encode(msg.as_bytes()).decode()
        try:
            res=service.users().messages().send(userId='me', body={'raw': raw}).execute()
            log(f"Sent {lead['hotel_name']} <{lead['email']}> ID {res['id']}")
            sent_now.append(lead)
            sent['sent'].append({'id':lead['id'],'hotel':lead['hotel_name'],'email':lead['email']})
        except Exception as e:
            log(f"Failed {lead['hotel_name']} {e}")
        time.sleep(2)
    open(SENT_LOG,'w',encoding='utf-8').write(json.dumps(sent, indent=2))
    log(f"Batch done sent {len(sent_now)}/{len(batch)}, total logged {len(sent['sent'])}")
    log("Step 5: Waiting for reply - do not send follow-up until reply received, check Gmail for replies via search")

if __name__=="__main__":
    log("=== Daily Auto Pipeline START ===")
    find_leads()
    serper_enrich()
    strict_verify_and_clean()
    sync_csv()
    push_to_sheet()
    send_verified()
    sync_csv()
    log("=== Daily Auto Pipeline END - waiting for replies ===")
