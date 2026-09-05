#!/usr/bin/env python3
"""
lead_manager.py - Hotel lead pipeline tracker (state machine).

Manages data/hotel_leads.json with a status state machine:
    identified -> emailed -> replied -> proposal -> closed_won
                                    -> lost
Stages to revisit automatically (follow_ups_due) and audit flags are computed
from saved dates.

Usage:
  python lead_manager.py list [--status identified|emailed|...] [--json]
  python lead_manager.py add  --name "Sunset Cove Resort" --city "Miami, FL" \
        --email "info@sunset.com" --phone "+1-305-555-0199" \
        --website "http://sunsetcoveresort.com" --notes "No booking engine"
  python lead_manager.py update <id> --status replied --notes "..."
  python lead_manager.py due [--days N]     # follow-ups coming due
  python lead_manager.py stats               # pipeline summary
  python lead_manager.py export <file.csv>   # export to CSV

Environment overrides:
  LEADS_HOME  - directory holding data/hotel_leads.json (skill root by default)
"""
import argparse, csv, json, os, sys, uuid
from datetime import datetime, timedelta

BASE = os.environ.get("LEADS_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE, "data")
LEADS_FILE = os.path.join(DATA_DIR, "hotel_leads.json")

VALID_STATUSES = ["identified", "emailed", "replied", "proposal", "closed_won", "lost"]
# statuses where a prospect is still actionable
OPEN_STATUSES = ["identified", "emailed", "replied", "proposal"]
DATE_FMT = "%Y-%m-%d"


def now():
    return datetime.now().strftime(DATE_FMT)


def load():
    if not os.path.exists(LEADS_FILE):
        return []
    with open(LEADS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(leads):
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = LEADS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)
    os.replace(tmp, LEADS_FILE)


def find(leads, lead_id):
    return next((l for l in leads if l.get("id") == lead_id), None)


def cmd_add(args):
    leads = load()
    lead = {
        "id": "lead-%s" % uuid.uuid4().hex[:6],
        "hotel_name": args.name,
        "city": args.city or "",
        "contact_name": args.contact or "Hotel Manager / Owner",
        "email": args.email or "",
        "phone": args.phone or "",
        "website": args.website or "",
        "current_web_status": args.status_note or "",
        "audit_notes": args.notes or "",
        "outreach_status": "identified",
        "date_added": now(),
        "last_action": now(),
        "follow_up_date": (datetime.now() + timedelta(days=args.follow_up or 3)).strftime(DATE_FMT),
        "emails_sent": 0,
        "history": [{"date": now(), "event": "Lead identified"}],
    }
    leads.append(lead)
    save(leads)
    print("Added %s (%s)" % (lead["id"], lead["hotel_name"]))


def cmd_update(args):
    leads = load()
    lead = find(leads, args.id)
    if not lead:
        sys.exit("Lead not found: %s" % args.id)
    if args.status:
        if args.status not in VALID_STATUSES:
            sys.exit("Invalid status %r. Valid: %s" % (args.status, ", ".join(VALID_STATUSES)))
        lead["outreach_status"] = args.status
    if args.notes:
        lead["audit_notes"] = args.notes
    lead["last_action"] = now()
    lead["history"] = lead.get("history", []) + [
        {"date": now(), "event": args.event or "Status updated"}]
    if args.follow_up:
        lead["follow_up_date"] = args.follow_up
    save(leads)
    print("Updated %s -> %s" % (args.id, lead["outreach_status"]))


def follow_up_due(lead, days):
    """True if a lead's follow_up_date is >=days in the past (or missing and old)."""
    if lead.get("outreach_status") not in OPEN_STATUSES:
        return False
    fud = lead.get("follow_up_date")
    if not fud:
        return True
    try:
        d = datetime.strptime(fud, DATE_FMT).date()
    except ValueError:
        return True
    return (datetime.now().date() - d).days >= days


def cmd_due(args):
    leads = load()
    due = [l for l in leads if follow_up_due(l, args.days)]
    if args.json:
        print(json.dumps(due, indent=2))
        return
    if not due:
        print("No follow-ups due within %s days." % args.days)
        return
    print("Follow-ups due (>= %s days past follow-up date):" % args.days)
    for l in due:
        print("  %-10s %-28s %-10s last: %s follow-up: %s" %
              (l["id"], l["hotel_name"][:28], l["outreach_status"], l.get("last_action"), l.get("follow_up_date")))


def cmd_list(args):
    leads = load()
    if args.status:
        leads = [l for l in leads if l["outreach_status"] == args.status]
    if args.json:
        print(json.dumps(leads, indent=2))
        return
    if not leads:
        print("No leads.")
        return
    hdr = "%-10s %-28s %-14s %-10s %-12s %s" % ("ID", "Hotel", "City", "Status", "Follow-up", "Email")
    print(hdr)
    print("-" * len(hdr))
    for l in leads:
        print("%-10s %-28s %-14s %-10s %-12s %s" %
              (l["id"], l["hotel_name"][:28], (l.get("city") or "")[:14],
               l["outreach_status"], l.get("follow_up_date") or "", l.get("email") or ""))


def cmd_stats(args):
    leads = load()
    from collections import Counter
    counts = Counter(l["outreach_status"] for l in leads)
    print("Total leads: %d" % len(leads))
    for s in VALID_STATUSES:
        bar = "#" * counts.get(s, 0)
        print("  %-12s %3d  %s" % (s, counts.get(s, 0), bar))


def cmd_export(args):
    leads = load()
    with open(args.filename, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=[
            "id", "hotel_name", "city", "contact_name", "email", "phone",
            "website", "current_web_status", "audit_notes", "outreach_status",
            "date_added", "last_action", "follow_up_date", "emails_sent"])
        w.writeheader()
        for l in leads:
            w.writerow({k: l.get(k, "") for k in w.fieldnames})
    print("Exported %d leads to %s" % (len(leads), args.filename))


def main():
    p = argparse.ArgumentParser(description="Hotel lead pipeline tracker")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("list"); sp.add_argument("--status"); sp.add_argument("--json", action="store_true"); sp.set_defaults(func=cmd_list)
    sp = sub.add_parser("add")
    sp.add_argument("--name", required=True); sp.add_argument("--city"); sp.add_argument("--contact")
    sp.add_argument("--email"); sp.add_argument("--phone"); sp.add_argument("--website")
    sp.add_argument("--status-note"); sp.add_argument("--notes"); sp.add_argument("--follow-up", type=int)
    sp.set_defaults(func=cmd_add)
    sp = sub.add_parser("update")
    sp.add_argument("id"); sp.add_argument("--status"); sp.add_argument("--notes")
    sp.add_argument("--event"); sp.add_argument("--follow-up")
    sp.set_defaults(func=cmd_update)
    sp = sub.add_parser("due"); sp.add_argument("--days", type=int, default=0); sp.add_argument("--json", action="store_true"); sp.set_defaults(func=cmd_due)
    sp = sub.add_parser("stats"); sp.set_defaults(func=cmd_stats)
    sp = sub.add_parser("export"); sp.add_argument("filename"); sp.set_defaults(func=cmd_export)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()