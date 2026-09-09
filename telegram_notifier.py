#!/usr/bin/env python3
"""
HERMES Telegram Notifier — sends updates to Telegram via Bot API.
"""
import json, os, requests
from datetime import datetime

CONFIG_FILE = r"C:/Users/AHMAD RAJA/Desktop/hermes/telegram_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, indent=2)

def send_message(bot_token, chat_id, text, parse_mode='HTML'):
    """Send message to Telegram."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode,
        'disable_web_page_preview': True
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.json()
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def format_lead_stats():
    """Get current pipeline stats."""
    try:
        import csv, json
        csv_leads = list(csv.DictReader(open(r'C:/Users/AHMAD RAJA/Desktop/hermes/indian_hotel_leads.csv', encoding='utf-8')))
        sent = json.load(open(r'C:/Users/AHMAD RAJA/Desktop/hermes/sent_log_goa_pune.json'))
        
        total = len(csv_leads)
        india = len([r for r in csv_leads if not (r.get('Lead ID','').startswith('us-') or r.get('id','').startswith('us-') or r.get('Lead ID','').startswith('us-serper'))])
        usa = total - india
        with_email = len([r for r in csv_leads if (r.get('Email Address','') or r.get('email','')).strip()])
        sent_count = len(sent.get('sent', []))
        
        return f"""📊 <b>HERMES Pipeline Status</b> — {datetime.now().strftime('%b %d, %H:%M')}

📈 <b>Leads:</b> {total} total ({india} India + {usa} USA)
📧 <b>With email:</b> {with_email}
📤 <b>Sent:</b> {sent_count} emails
🇺🇸 <b>USA ready:</b> {len([r for r in csv_leads if (r.get('Lead ID','').startswith('us-') or r.get('id','').startswith('us-') or r.get('Lead ID','').startswith('us-serper')) and (r.get('Email Address','') or r.get('email','')).strip()])} verified
"""
    except Exception as e:
        return f"📊 Pipeline status error: {e}"

def send_pipeline_update():
    """Send full pipeline update to Telegram."""
    config = load_config()
    bot_token = config.get('bot_token')
    chat_id = config.get('chat_id')
    
    if not bot_token or not chat_id:
        return {'ok': False, 'error': 'Telegram not configured. Run setup_telegram() first.'}
    
    text = format_lead_stats()
    return send_message(bot_token, chat_id, text)

def send_alert(bot_token, chat_id, title, message):
    """Send alert message."""
    text = f"🚨 <b>{title}</b>\n\n{message}"
    return send_message(bot_token, chat_id, text)

def send_reply_alert(bot_token, chat_id, hotel_name, classification, from_email, preview):
    """Send alert for new reply."""
    emoji = {
        'INTERESTED': '🔥',
        'DEMO_REQUEST': '🎯',
        'PRICE_REQUEST': '💰',
        'QUESTION': '❓',
        'NOT_INTERESTED': '❌',
        'UNSUBSCRIBE': '🛑',
        'WRONG_PERSON': '🔄',
        'UNCLEAR': '🤔'
    }.get(classification, '📨')
    
    text = f"""{emoji} <b>New Reply: {classification}</b>

🏨 <b>Hotel:</b> {hotel_name}
📧 <b>From:</b> {from_email}
📝 <b>Preview:</b> {preview[:200]}...
"""
    return send_message(bot_token, chat_id, text)

def send_demo_alert(bot_token, chat_id, hotel_name, demo_url):
    """Send alert when demo is ready."""
    text = f"""✅ <b>Demo Ready</b>

🏨 <b>Hotel:</b> {hotel_name}
🔗 <b>Demo URL:</b> {demo_url}

Sent to client.
"""
    return send_message(bot_token, chat_id, text)

def setup_telegram(bot_token, chat_id):
    """Configure Telegram bot."""
    config = {'bot_token': bot_token, 'chat_id': chat_id, 'setup_date': datetime.now().isoformat()}
    save_config(config)
    # Test
    result = send_message(bot_token, chat_id, "✅ HERMES Telegram connected!")
    return result

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'setup':
        if len(sys.argv) >= 4:
            print(json.dumps(setup_telegram(sys.argv[2], sys.argv[3]), indent=2))
        else:
            print("Usage: python telegram_notifier.py setup <bot_token> <chat_id>")
    elif len(sys.argv) > 1 and sys.argv[1] == 'test':
        config = load_config()
        print(json.dumps(send_message(config.get('bot_token'), config.get('chat_id'), "🧪 HERMES test message"), indent=2))
    else:
        print(json.dumps(send_pipeline_update(), indent=2))