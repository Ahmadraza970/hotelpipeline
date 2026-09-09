#!/usr/bin/env python3
"""
HERMES Reply Handler — Monitors Gmail, classifies replies, updates leads, prepares responses.
"""
import json, csv, os, re, base64
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

HERMES_DIR = os.environ.get("HERMES_DIR", os.path.expanduser("~"))
CSV = os.path.join(HERMES_DIR, "indian_hotel_leads.csv")
SENT_LOG = os.path.join(HERMES_DIR, "sent_log_goa_pune.json")
TOKEN = os.path.join(HERMES_DIR, "google_token.json")
SHEET_ID = "1wt74LQbaVKT4um2Auv92lJDWF0lKj7_JejnrRBi26cY"

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/spreadsheets'
]

# Reply classification patterns
INTEREST_PATTERNS = [
    r'\b(interested|demo|show me|can you|send me|sample|example|see it|look at)\b',
    r'\b(how much|price|cost|pricing|budget|quote|estimate)\b',
    r'\b(want|need|would like|looking for|considering)\b',
    r'\b(tell me more|more info|details|information)\b',
]

QUESTION_PATTERNS = [
    r'\b(what|how|when|where|who|which)\b.*\?',
    r'\b(can you|could you|would you)\b',
]

NOT_INTERESTED_PATTERNS = [
    r'\b(not interested|no thanks|don\'t need|no need|already have|already using)\b',
    r'\b(happy with|satisfied with|don\'t want)\b',
]

UNSUBSCRIBE_PATTERNS = [
    r'\b(unsubscribe|remove|stop|opt.?out|don\'t contact|do not contact|no more)\b',
]

WRONG_PERSON_PATTERNS = [
    r'\b(wrong person|not the right|not responsible|forward|someone else)\b',
]

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def load_sent_log():
    with open(SENT_LOG, encoding='utf-8') as f:
        return json.load(f)

def load_csv():
    rows = list(csv.DictReader(open(CSV, encoding='utf-8')))
    # Handle both internal format (id, hotel_name, etc.) and Sheet format (Lead ID, Hotel Name, etc.)
    result = {}
    for r in rows:
        # Map Sheet headers to internal keys
        lead_id = r.get('id') or r.get('Lead ID') or r.get('lead_id')
        hotel_name = r.get('hotel_name') or r.get('Hotel Name') or r.get('hotel name')
        city = r.get('city') or r.get('City / Destination') or r.get('city / destination')
        phone = r.get('phone') or r.get('Phone Number') or r.get('phone number')
        email = r.get('email') or r.get('Email Address') or r.get('email address')
        website = r.get('website') or r.get('Website Status') or r.get('website status')
        status = r.get('status') or r.get('Lead Status') or r.get('lead status')
        date_discovered = r.get('date_discovered') or r.get('Date Discovered') or r.get('date discovered')
        audit_notes = r.get('audit_notes') or r.get('Audit & Pitch Notes') or r.get('audit & pitch notes')
        last_reply_date = r.get('last_reply_date') or r.get('Last Reply') or r.get('last reply')
        reply_classification = r.get('reply_classification') or r.get('Reply Classification') or r.get('reply classification')
        reply_body = r.get('reply_body') or r.get('Reply Body') or r.get('reply body')
        reply_date = r.get('reply_date') or r.get('Reply Date') or r.get('reply date')
        response_draft = r.get('response_draft') or r.get('Response Draft') or r.get('response draft')
        
        if lead_id:
            result[lead_id] = {
                'id': lead_id,
                'hotel_name': hotel_name,
                'city': city,
                'phone': phone,
                'email': email,
                'website': website,
                'status': status,
                'date_discovered': date_discovered,
                'audit_notes': audit_notes,
                'last_reply_date': last_reply_date,
                'reply_classification': reply_classification,
                'reply_body': reply_body,
                'reply_date': reply_date,
                'response_draft': response_draft
            }
    return result

def save_csv(leads_dict):
    FIELDNAMES = ['id','hotel_name','city','phone','email','website','status','date_discovered','audit_notes','last_reply_date','reply_classification','reply_body','reply_date','response_draft']
    rows = sorted(leads_dict.values(), key=lambda x: x['id'])
    with open(CSV, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows([{k: r.get(k, '') for k in FIELDNAMES} for r in rows])

def get_gmail_service():
    creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    return build('gmail', 'v1', credentials=creds)

def classify_reply(body_text):
    """Classify reply intent based on content."""
    text = body_text.lower()
    
    # Check unsubscribe first
    for pat in UNSUBSCRIBE_PATTERNS:
        if re.search(pat, text):
            return 'UNSUBSCRIBE'
    
    # Check not interested
    for pat in NOT_INTERESTED_PATTERNS:
        if re.search(pat, text):
            return 'NOT_INTERESTED'
    
    # Check wrong person
    for pat in WRONG_PERSON_PATTERNS:
        if re.search(pat, text):
            return 'WRONG_PERSON'
    
    # Check price request
    for pat in [r'\b(price|cost|pricing|budget|quote|estimate)\b']:
        if re.search(pat, text):
            return 'PRICE_REQUEST'
    
    # Check demo request
    for pat in [r'\b(demo|sample|example|show me|see it)\b']:
        if re.search(pat, text):
            return 'DEMO_REQUEST'
    
    # Check general interest
    for pat in INTEREST_PATTERNS:
        if re.search(pat, text):
            return 'INTERESTED'
    
    # Check questions
    for pat in QUESTION_PATTERNS:
        if re.search(pat, text):
            return 'QUESTION'
    
    return 'UNCLEAR'

def extract_body(payload):
    """Extract plain text body from Gmail payload."""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain' and 'data' in part.get('body', {}):
                return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
            elif 'parts' in part:
                result = extract_body(part)
                if result:
                    return result
    elif payload['mimeType'] == 'text/plain' and 'data' in payload.get('body', {}):
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
    return ''

def get_recent_replies(service, sent_ids, days_back=7):
    """Fetch recent emails that might be replies to our sent emails."""
    query = f'newer_than:{days_back}d in:inbox'
    results = service.users().messages().list(userId='me', q=query, maxResults=100).execute()
    messages = results.get('messages', [])
    
    replies = []
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        headers = {h['name']: h['value'] for h in msg_data['payload'].get('headers', [])}
        
        # Check if it's a reply to our sent email
        in_reply_to = headers.get('In-Reply-To', '')
        references = headers.get('References', '')
        subject = headers.get('Subject', '')
        from_email = headers.get('From', '')
        body = extract_body(msg_data['payload'])
        
        # Match to sent log by Message-ID in References/In-Reply-To
        matched_lead = None
        for sent_id in sent_ids:
            if sent_id in references or sent_id in in_reply_to:
                matched_lead = sent_id
                break
        
        # Also match by email + subject similarity
        if not matched_lead:
            for sent in load_sent_log()['sent']:
                if sent['email'].lower() in from_email.lower():
                    matched_lead = sent['id']
                    break
        
        if matched_lead:
            replies.append({
                'lead_id': matched_lead,
                'message_id': msg['id'],
                'thread_id': msg_data.get('threadId'),
                'from': from_email,
                'subject': subject,
                'body': body[:2000],
                'date': headers.get('Date', ''),
                'in_reply_to': in_reply_to,
                'references': references
            })
    
    return replies

def update_lead_status(leads_dict, lead_id, status, reply_classification=None):
    if lead_id in leads_dict:
        leads_dict[lead_id]['status'] = status
        leads_dict[lead_id]['last_reply_date'] = datetime.now().strftime('%Y-%m-%d')
        if reply_classification:
            leads_dict[lead_id]['reply_classification'] = reply_classification
        return True
    return False

def push_to_sheet(leads_dict):
    """Push updated leads to Google Sheet."""
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    try:
        creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
        svc = build('sheets', 'v4', credentials=creds)
        
        rows = sorted(leads_dict.values(), key=lambda x: x['id'])
        vals = [['Lead ID','Hotel Name','City / Destination','Phone Number','Email Address','Website Status','OTA Commission Loss','Lead Status','Date Discovered','Audit & Pitch Notes','Last Reply','Reply Classification']]
        for r in rows:
            vals.append([
                r.get('id',''), r.get('hotel_name',''), r.get('city',''),
                r.get('phone') or 'Not listed', r.get('email') or 'Pending lookup',
                'NO WEBSITE (OTA Only)' if not r.get('website') else r.get('website'),
                '15% - 25%' if r.get('city') in ['New York','Miami','Orlando','Los Angeles','San Francisco','Austin','New Orleans','Seattle','Denver','Las Vegas','Chicago','Boston','San Francisco'] else '18% - 22%',
                r.get('status','identified').upper(), r.get('date_discovered',''),
                r.get('audit_notes',''), r.get('last_reply_date',''),
                r.get('reply_classification','')
            ])
        
        svc.spreadsheets().values().clear(spreadsheetId=SHEET_ID, range='Sheet1!A1:L1000').execute()
        for i in range(0, len(vals), 200):
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID, range=f'Sheet1!A{i+1}', valueInputOption='RAW',
                body={'values': vals[i:i+200]}
            ).execute()
        log(f"Pushed {len(vals)-1} leads to Sheet")
    except Exception as e:
        log(f"Sheet push failed (continuing): {e}")

def prepare_response(lead, classification):
    """Generate response draft based on classification."""
    hotel = lead['hotel_name']
    city = lead['city']
    
    templates = {
        'INTERESTED': f"""Subject: Re: Demo for {hotel} - Quick Video & Link

Hi there,

Thanks for your interest! I've prepared a personalized demo for {hotel} based on our master template.

Demo link: [DEPLOY_URL_WHEN_READY]
Quick 2-min walkthrough video: [VIDEO_URL_IF_AVAILABLE]

The demo shows your hotel with direct booking, commission-free payments, and guest reviews — all in the same professional design.

Would you like to hop on a 10-min call this week to walk through it? I'm flexible.

Best,
Miths James
+91 9835685952
mithsjames87@gmail.com""",
        
        'PRICE_REQUEST': f"""Subject: Re: Pricing for {hotel} - Direct Booking Website

Hi,

Great question. Our pricing is designed to pay for itself from commission savings:

**Package 1: Essential** (Guesthouses/Inns) — ₹8,000–₹9,500 one-time
- Mobile website + direct booking engine + UPI/card payments + review showcase
- Live in 5–7 days

**Package 2: Growth** (Boutique Hotels/Resorts) — ₹12,000–₹15,000 one-time
- Everything above + channel manager sync (MakeMyTrip/Booking.com) + SEO + 30-day support

ROI: At ₹2,500/night, saving just 3 direct bookings/month covers the entire cost.

Want to see a demo for {hotel} first? I can send a personalized link.

Best,
Miths James
+91 9835685952""",
        
        'DEMO_REQUEST': f"""Subject: Re: Your Demo for {hotel} is Ready

Hi,

Your personalized demo for {hotel} is live:

🔗 [DEPLOY_URL_WHEN_READY]

It shows:
- Direct booking engine (UPI/card, no commission)
- Guest review showcase (Google/TripAdvisor)
- Mobile-first design
- Your verified info: {city}, {lead.get('phone','')}, {lead.get('email','')}

Take a look on mobile and desktop. Happy to walk you through on a quick call.

Best,
Miths James""",
        
        'QUESTION': f"""Subject: Re: Your Question about {hotel}

Hi,

Thanks for reaching out. Happy to clarify — what specific question did you have?

If it's about pricing, timeline, features, or how the booking engine works with your current OTAs, just let me know.

Best,
Miths James""",
        
        'NOT_INTERESTED': f"""Subject: Re: {hotel} - No Problem

Understood — no worries at all. I'll mark {hotel} as not interested and won't follow up.

If things change down the line, feel free to reach out.

Best,
Miths James""",
        
        'WRONG_PERSON': f"""Subject: Re: {hotel} - Right Contact?

No problem — could you point me to the right person who handles website/marketing decisions for {hotel}?

Thanks,
Miths James""",
        
        'UNSUBSCRIBE': f"""Subject: Re: Unsubscribed - {hotel}

You've been unsubscribed. No further emails will be sent to {lead.get('email')}.

Best,
Miths James""",
    }
    
    return templates.get(classification, templates['QUESTION'])

def process_replies():
    log("=== HERMES REPLY HANDLER START ===")
    
    # Load data
    sent_log = load_sent_log()
    sent_ids = {s['id'] for s in sent_log['sent']}
    leads = load_csv()
    
    # Get Gmail service
    service = get_gmail_service()
    
    # Fetch recent replies
    replies = get_recent_replies(service, sent_ids, days_back=7)
    log(f"Found {len(replies)} potential replies")
    
    if not replies:
        log("No new replies")
        return
    
    updated = 0
    for reply in replies:
        lead_id = reply['lead_id']
        if lead_id not in leads:
            log(f"Lead {lead_id} not in CSV, skipping")
            continue
        
        lead = leads[lead_id]
        classification = classify_reply(reply['body'])
        
        log(f"Reply from {lead['hotel_name']} ({lead_id}): {classification}")
        log(f"  From: {reply['from']}")
        log(f"  Subject: {reply['subject']}")
        log(f"  Body preview: {reply['body'][:200]}")
        
        # Update lead status
        status_map = {
            'INTERESTED': 'INTERESTED',
            'DEMO_REQUEST': 'DEMO_REQUEST',
            'PRICE_REQUEST': 'PRICE_REQUEST',
            'QUESTION': 'QUESTION',
            'NOT_INTERESTED': 'NOT_INTERESTED',
            'WRONG_PERSON': 'WRONG_PERSON',
            'UNSUBSCRIBE': 'DO_NOT_CONTACT',
            'UNCLEAR': 'REPLIED'
        }
        new_status = status_map.get(classification, 'REPLIED')
        
        if update_lead_status(leads, lead_id, new_status, classification):
            updated += 1
            
            # Save response draft to lead
            response_draft = prepare_response(lead, classification)
            leads[lead_id]['response_draft'] = response_draft
            leads[lead_id]['reply_body'] = reply['body'][:1000]
            leads[lead_id]['reply_date'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # Mark Gmail as read (optional)
        try:
            service.users().messages().modify(
                userId='me', id=reply['message_id'],
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
        except:
            pass
    
    # Save CSV
    if updated:
        save_csv(leads)
        log(f"Updated {updated} leads in CSV")
        
        # Push to Sheet
        push_to_sheet(leads)
    
    log("=== REPLY HANDLER COMPLETE ===")
    return replies

if __name__ == '__main__':
    process_replies()