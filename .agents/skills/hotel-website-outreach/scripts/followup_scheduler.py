#!/usr/bin/env python3
"""
followup_scheduler.py - Polite follow-up planner.

Reads data/hotel_leads.json and reports which open leads are due a follow-up
based on their follow_up_date / last_action. Follow-ups are spaced 4-5 days
per the skill's best practices; a lead gets 1-2 before it's parked.

With --render, it prints a ready-to-send follow-up email body (dry-run) so you
can review before sending via outreach_sender.py or your mail client.

Usage:
  python followup_scheduler.py                  # list who needs a follow-up today
  python followup_scheduler.py --due 5          # due within 5 days
  python followup_scheduler.py --render         # also render a follow-up email
  python followup_scheduler.py --render --id lead-abc123
"""
import argparse, json, os, sys
from datetime import datetime

BASE = os.environ.get("LEADS_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEADS_FILE = os.path.join(BASE, "data", "hotel_leads.json")

OPEN = ["identified", "emailed", "replied", "proposal"]
FOLLOWUP_BODY = """Hi {contact_name},

Just following up on my earlier note about a direct booking system for {hotel_name}. I know you're busy, so I'll keep it short.

Hotels that move even a slice of their OTA bookings onto their own site keep that {comm_pct}% commission as pure profit. Happy to send a 2-minute video walkthrough or a tailored demo whenever suits.

If now isn't the right time, no problem — just let me know and I'll leave it there.

Best regards,
{from_name}"""


def load_leads():
    if not os.path.exists(LEADS_FILE):
        sys.exit("No leads file found at %s" % LEADS_FILE)
    with open(LEADS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_cfg():
    cfg_path = os.path.join(BASE, "data", "config.json")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def days_since(date_str):
    try:
        return (datetime.now().date() - datetime.strptime(date_str, "%Y-%m-%d").date()).days
    except (ValueError, TypeError):
        return 999


def main():
    p = argparse.ArgumentParser(description="Hotel follow-up scheduler")
    p.add_argument("--due", type=int, default=0, help="Due if follow_up_date is this many days in the past or more (default 0 = due today or overdue)")
    p.add_argument("--render", action="store_true", help="Also render a follow-up email")
    p.add_argument("--id", help="Render follow-up only for this lead")
    args = p.parse_args()

    leads = load_leads()
    cfg = load_cfg()
    due = [l for l in leads if l["outreach_status"] in OPEN and days_since(l.get("follow_up_date") or l["date_added"]) >= args.due]
    due.sort(key=lambda l: l.get("follow_up_date") or "9999-01-01")

    if not due:
        print("No follow-ups due (threshold %s days)." % args.due)
        return

    print("Follow-ups due (threshold %s days): %d" % (args.due, len(due)))
    print("%-10s %-28s %-10s follow-up due" % ("ID", "Hotel", "Status"))
    print("-" * 62)
    for l in due:
        if args.id and l["id"] != args.id:
            continue
        print("%-10s %-28s %-10s %s" % (l["id"], l["hotel_name"][:28], l["outreach_status"], l.get("follow_up_date")))
        if args.render:
            comm_pct = int((l.get("assumed_commission") or 0.18) * 100)
            body = FOLLOWUP_BODY.format(
                contact_name=l.get("contact_name", "there"),
                hotel_name=l.get("hotel_name", "your hotel"),
                comm_pct=comm_pct,
                from_name=cfg.get("from_name", "Your Name / Agency"))
            print()
            print("  --- follow-up for %s <%s> ---" % (l["hotel_name"], l.get("email")))
            print("  " + body.replace("\n", "\n  "))
            print()


if __name__ == "__main__":
    main()