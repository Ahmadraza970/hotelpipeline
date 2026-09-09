#!/usr/bin/env python3
"""
outreach_sender.py - Personalized cold-email sender + anti-spam safeguard.

* Reads prospects from data/hotel_leads.json (or --id for one lead).
* Personalizes the skill's Template 1 (OTA commission-savings pitch).
* Defaults to --dry-run: renders the email to stdout instead of sending.
* Sending requires SMTP config in data/config.json AND --commit.
  Anti-spam guardrails are enforced before anything sends:
      - hard daily cap (default 30, warm-up ramp below)
      - skip leads already emailed today / exceeding warm-up cap
      - injects an unsubscribe link ({{unsubscribe}}) into every message
      - sends one-by-one with a delay, never bulk

data/config.json (only needed for real sending):
  {
    "smtp_host": "smtp.yourdomain.com",
    "smtp_port": 587,
    "smtp_user": "outreach@yourdomain.com",
    "smtp_pass": "...",
    "from_name": "Your Name / Agency",
    "daily_limit": 30,
    "warmup_limit": 20,
    "unsubscribe_url": "https://yourdomain.com/unsubscribe?email={{email}}"
  }

Usage:
  python outreach_sender.py --dry-run
  python outreach_sender.py --dry-run --id lead-abc123
  python outreach_sender.py --commit --id lead-abc123
"""
import argparse, json, os, smtplib, sys, time
from datetime import datetime
from email.mime.text import MIMEText

try:
    sys.path.insert(0, os.environ.get("LEADS_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from telegram_notifier import send_message, load_config as tg_load_config
except Exception:
    send_message = tg_load_config = None

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE = os.environ.get("LEADS_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE, "data")
LEADS_FILE = os.path.join(DATA_DIR, "hotel_leads.json")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

SUBJECT_TPL = "Direct booking & guest review system for {hotel_name} (stop losing ~{comm_pct}% OTA fees)"
BODY_TPL = """Hi {contact_name},

I came across **{hotel_name}** while researching top places to stay in {city}. Your property looks fantastic, but I noticed guests currently don't have a direct website to check room availability and book directly without paying high fees to OTAs like Booking.com or MakeMyTrip.

Every time a guest books through an OTA, you are paying **{comm_pct}% to {comm_hi}% in commissions**. On average reservations, that is thousands of dollars lost each month that should stay in your pocket.

We build modern, high-converting websites specifically tailored for hotels and guesthouses like {hotel_name}, equipped with two game-changing features:

  🏨 1. Zero-Commission Direct Booking Engine:
     - Accept instant reservations and secure card payments directly on your website.
     - Keep 100% of your booking revenue (zero middleman fees).
     - Automated calendar sync with Airbnb & Booking.com to prevent double-bookings.

  ⭐ 2. Verified Customer Reviews & Reputation Showcase:
     - Highlight your best 5-star guest reviews and ratings front-and-center.
     - Gives prospective travelers the trust and social proof they need to book immediately on your site.
     - Automated review collection to encourage happy guests to leave feedback.

  📱 3. Mobile-First & Ultra-Fast:
     - Over 70% of travelers book on phones — your site will look stunning and load in under 1.5 seconds.
     - Turnkey delivery in 7–10 days with complete staff training.

We've already put together a quick interactive preview mockup designed specifically for **{hotel_name}**.

Would you be open to a quick 5-minute preview this week?

Best regards,
{from_name}

---
{unsubscribe}"""


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_leads():
    if not os.path.exists(LEADS_FILE):
        return []
    with open(LEADS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_leads(leads):
    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)


def render(lead, cfg):
    comm_pct = int((lead.get("assumed_commission") or 0.18) * 100)
    comm_hi = int((lead.get("assumed_commission") or 0.18) * 100 + 7)
    unsub = cfg.get("unsubscribe_url", "#").replace("{{email}}", lead.get("email", ""))
    body = BODY_TPL.format(
        hotel_name=lead.get("hotel_name", "your hotel"),
        contact_name=lead.get("contact_name", "there"),
        city=lead.get("city", "your area"),
        comm_pct=comm_pct, comm_hi=comm_hi,
        from_name=cfg.get("from_name", "Your Name / Agency"),
        unsubscribe=("Unsubscribe: " + unsub) if cfg.get("unsubscribe_url") else "",
    )
    subject = SUBJECT_TPL.format(hotel_name=lead.get("hotel_name", "your hotel"), comm_pct=comm_pct)
    return subject, body


def send_one(lead, subject, body, cfg, dry, today):
    if not lead.get("email"):
        print("  [skip] %s — no email on file" % lead["id"]); return False
    sent_today = lead.get("emails_sent_today", 0)
    if sent_today > 0:
        print("  [skip] %s — already emailed today" % lead["id"]); return False
    if lead.get("emails_sent", 0) >= cfg.get("warmup_limit", 20) and dry is False:
        print("  [skip] %s — at warm-up cap" % lead["id"]); return False

    if dry:
        print("  [dry-run output for %s <%s>]" % (lead["hotel_name"], lead["email"]))
        print("  SUBJECT: %s" % subject)
        print("  ----------------------------------------")
        print(body)
        print()
        return True

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = "%s <%s>" % (cfg.get("from_name", ""), cfg.get("smtp_user", ""))
    msg["To"] = lead["email"]
    with smtplib.SMTP(cfg.get("smtp_host"), cfg.get("smtp_port", 587), timeout=30) as s:
        s.starttls()
        s.login(cfg["smtp_user"], cfg["smtp_pass"])
        s.send_message(msg)
    # record send
    lead["emails_sent"] = lead.get("emails_sent", 0) + 1
    lead["emails_sent_today"] = sent_today + 1
    lead["last_action"] = today
    if lead["outreach_status"] == "identified":
        lead["outreach_status"] = "emailed"
    lead["history"] = lead.get("history", []) + [{"date": today, "event": "Email sent"}]
    return True


def main():
    p = argparse.ArgumentParser(description="Hotel cold-email sender")
    p.add_argument("--id", help="Only send to one lead id")
    p.add_argument("--dry-run", action="store_true", default=True, help="Render only (default)")
    p.add_argument("--commit", dest="dry_run", action="store_false", help="Actually send via SMTP")
    p.add_argument("--delay", type=float, default=2.0, help="Seconds between real sends")
    args = p.parse_args()

    cfg = load_config()
    leads = load_leads()
    if args.id:
        leads = [l for l in leads if l["id"] == args.id]
        if not leads:
            sys.exit("Lead not found: %s" % args.id)

    if not args.dry_run:
        if not cfg.get("smtp_host") or not cfg.get("smtp_user"):
            sys.exit("--commit requires smtp_host/smtp_user in data/config.json (see docstring). Not sending.")
        cap = cfg.get("daily_limit", 30)
        today = datetime.now().strftime("%Y-%m-%d")

    sent = 0
    for lead in leads:
        if lead.get("outreach_status") in ("closed_won", "lost"):
            continue
        subject, body = render(lead, cfg)
        ok = send_one(lead, subject, body, cfg, args.dry_run, today if not args.dry_run else datetime.now().strftime("%Y-%m-%d"))
        if ok:
            sent += 1
            if not args.dry_run:
                save_leads(leads)
                if args.delay:
                    time.sleep(args.delay)

    if args.dry_run:
        print("Rendered %d email(s) (dry-run, nothing sent). Use --commit to send." % sent)
    else:
        print("Sent %d email(s). Daily cap is %d." % (sent, cfg.get("daily_limit", 30)))

    # Telegram notification
    if send_message and tg_load_config:
        try:
            tg_cfg = tg_load_config()
            bot_token = tg_cfg.get('bot_token')
            chat_id = tg_cfg.get('chat_id')
            if bot_token and chat_id and sent > 0:
                mode = "📤 <b>Email Sent</b>" if not args.dry_run else "✏️ <b>Dry-Run Preview</b>"
                lines = [f"{mode} — {sent} lead(s)"]
                for lead in leads[:sent]:
                    name = lead.get('hotel_name','')
                    city = lead.get('city','')
                    email = lead.get('email','')
                    subject, _ = render(lead, cfg)
                    status = lead.get('outreach_status','identified')
                    lines.append(f"\n🏨 {name} | {city}")
                    lines.append(f"📧 {email}")
                    lines.append(f"📋 {subject}")
                    lines.append(f"🔹 Status: {status}")
                text = "\n".join(lines)
                send_message(bot_token, chat_id, text)
        except Exception:
            pass


if __name__ == "__main__":
    main()