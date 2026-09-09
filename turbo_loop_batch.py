import csv, json, os, re, time, base64, sys, urllib.request
from datetime import datetime
HERMES_DIR = r"C:/Users/AHMAD RAJA/Desktop/hermes"
CSV = os.path.join(HERMES_DIR, "indian_hotel_leads.csv")
SENT_LOG = os.path.join(HERMES_DIR, "sent_log_goa_pune.json")
SERPER_KEY = "d0f391c08934a027ae79ef736de987af6a16de36"
GOOGLE_TOKEN = "C:/Users/AHMAD RAJA/AppData/Local/hermes/google_token.json"
def log(m): print(f"[{datetime.now().strftime('%H:%M:%S')}] {m}", flush=True)
def s_search(q):
    d=json.dumps({'q':q,'num':5}).encode()
    req=urllib.request.Request('https://google.serper.dev/search', data=d, headers={'X-API-KEY':SERPER_KEY,'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())
def ext_email(t):
    ms=re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', t)
    filt=[e for e in ms if 'info@gmail.com' not in e.lower() and 'example' not in e.lower()]
    pref=[e for e in filt if any(k in e.lower() for k in ['contact','info','reservation','booking','sales'])]
    return (pref[0] if pref else (filt[0] if filt else ''))
import subprocess as sp
def mx_ok(domain):
    try:
        out=sp.run(['nslookup','-type=mx',domain,'8.8.8.8'], capture_output=True, text=True, timeout=8)
        if 'mail exchanger' in out.stdout.lower(): return True
        if 'non-existent domain' in out.stdout.lower() or "can't find" in out.stdout.lower(): return False
        return False
    except: return False

rows=list(csv.DictReader(open(CSV, encoding='utf-8')))
targets=[r for r in rows if not r['email'].strip()][:25]
if not targets:
    log("No targets")
    sys.exit(0)
log(f"BATCH enriching {len(targets)} (no sleep)")
updated=0
id_map={r['id']:r for r in targets}
for lead in targets:
    q=f"{lead['hotel_name']} {lead['city']} contact email phone"
    try:
        res=s_search(q)
        blob=' '.join([(o.get('snippet','')+' '+o.get('link','')) for o in res.get('organic',[])])
        email=ext_email(blob)
        if email: lead['email']=email; updated+=1
        log(f"  {lead['hotel_name'][:22]} -> {email or '-'}")
    except Exception as e: log(f"  err {lead['hotel_name']} {e}")
FIELDNAMES=['id','hotel_name','city','phone','email','website','status','date_discovered','audit_notes']
for r in rows:
    if r['id'] in id_map: r['email']=id_map[r['id']]['email']
rows.sort(key=lambda x: x['id'])
with open(CSV,'w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f, fieldnames=FIELDNAMES); w.writeheader(); w.writerows([{k:r.get(k,'') for k in FIELDNAMES} for r in rows])
log(f"enriched {updated}/{len(targets)}")
# verify
rows=list(csv.DictReader(open(CSV, encoding='utf-8')))
cleaned=0
for r in rows:
    if r['email'].strip():
        d=r['email'].split('@')[-1]
        if d.lower() in ['hotelgreenparkgoa.com','gtdchotel.com'] or 'commonfloor.com' in d.lower():
            r['email']=''; cleaned+=1
        elif not mx_ok(d):
            r['email']=''; cleaned+=1
with open(CSV,'w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f, fieldnames=FIELDNAMES); w.writeheader(); w.writerows([{k:r.get(k,'') for k in FIELDNAMES} for r in rows])
log(f"cleaned {cleaned}, total with email {sum(1 for r in rows if r['email'].strip())}")
# send
rows=list(csv.DictReader(open(CSV, encoding='utf-8')))
try: sent=json.load(open(SENT_LOG,encoding='utf-8')); sent_ids=set(s['id'] for s in sent['sent'])
except: sent={'sent':[]}; sent_ids=set()
cands=[r for r in rows if r['email'].strip() and r['id'] not in sent_ids]
cands.sort(key=lambda x: (0 if x['city'].lower() in ('goa','pune','jaipur','manali') else 1, x['id']))
batch=cands[:25]
log(f"sending {len(batch)}")
if batch:
    from google.oauth2.credentials import Credentials; from googleapiclient.discovery import build; from email.mime.text import MIMEText
    creds=Credentials.from_authorized_user_file(GOOGLE_TOKEN, ['https://www.googleapis.com/auth/gmail.send'])
    service=build('gmail','v1', credentials=creds)
    tmpl="Namaste {hotel_name} in {city},\\n\\nDirect booking website saves 20% commission. Demo? - Ahmad +91 9835685952"
    try:
        t=open(os.path.join(HERMES_DIR,"daily_auto_pipeline.py"),encoding='utf-8').read()
        tmpl=t.split("template='''")[1].split("'''")[0]
    except: pass
    for lead in batch:
        body=tmpl.format(hotel_name=lead['hotel_name'], city=lead['city'])
        subject=f"Stop paying 20% MakeMyTrip/Goibibo commissions - Direct Booking & Review System for {lead['hotel_name']}"
        msg=MIMEText(body,'plain','utf-8'); msg['To']=lead['email']; msg['From']='Miths James <mithsjames87@gmail.com>'; msg['Subject']=subject
        raw=base64.urlsafe_b64encode(msg.as_bytes()).decode()
        try:
            res=service.users().messages().send(userId='me', body={'raw': raw}).execute()
            log(f" SENT {lead['hotel_name']} {lead['email']} {res['id']}")
            sent['sent'].append({'id':lead['id'],'hotel':lead['hotel_name'],'email':lead['email']})
        except Exception as e: log(f" FAILED {lead['hotel_name']} {e}")
    open(SENT_LOG,'w',encoding='utf-8').write(json.dumps(sent, indent=2))
    log(f"sent total {len(sent['sent'])}")
# sync
rows=list(csv.DictReader(open(CSV, encoding='utf-8')))
try: sent=json.load(open(SENT_LOG,encoding='utf-8')); sent_map={s['id']:s['email'] for s in sent['sent']}; sent_ids=set(sent_map)
except: sent_map={}; sent_ids=set()
for r in rows:
    if r['id'] in sent_ids:
        r['status']='sent'
        if r['id'] in sent_map: r['email']=sent_map[r['id']]
with open(CSV,'w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f, fieldnames=FIELDNAMES); w.writeheader(); w.writerows([{k:r.get(k,'') for k in FIELDNAMES} for r in rows])
log("DONE batch")
