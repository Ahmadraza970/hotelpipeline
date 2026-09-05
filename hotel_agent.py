#!/usr/bin/env python3
"""
hotel_agent.py - Master Hotel Lead Generation & Contract Closer Agent.

An end-to-end autonomous agent for:
  1. Finding hotels that lack websites or rely strictly on OTAs.
  2. Sending personalized cold emails pitching a custom site with a direct booking engine and customer review system.
  3. Handling replies, overcoming client objections, and generating ready-to-sign web development contracts.
  4. Launching an interactive CRM dashboard.

Usage:
  python hotel_agent.py find --city "Goa" [--limit 10] [--add]
  python hotel_agent.py list [--status identified|emailed|replied|proposal]
  python hotel_agent.py pitch --id lead-001 [--commit]
  python hotel_agent.py reply --id lead-001 [--intent price|ota_objection|demo_interest|no_need|contract_ready] [--text "..."]
  python hotel_agent.py contract --id lead-001 [--price 35000] [--currency INR] [--out contract.md]
  python hotel_agent.py dashboard [--port 8080]
"""
import argparse, json, os, subprocess, sys, webbrowser
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(ROOT_DIR, ".agents", "skills", "hotel-website-outreach")
SCRIPTS_DIR = os.path.join(SKILL_DIR, "scripts")
DATA_DIR = os.path.join(SKILL_DIR, "data")
LEADS_FILE = os.path.join(DATA_DIR, "hotel_leads.json")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")


def load_leads():
    if os.path.exists(LEADS_FILE):
        with open(LEADS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_leads(leads):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)


def cmd_find(args):
    from scripts.prospect_finder import find_osm
    print(f"[*] Scanning hospitality listings in '{args.city}' lacking official websites...")
    results = find_osm(args.city, limit=args.limit)
    if not results:
        print(f"No unqualified hotels found in {args.city}.")
        return

    print(f"\nDiscovered {len(results)} candidate hotels/guesthouses in {args.city}:\n")
    print("%-36s | %-16s | Phone: %-15s | Website" % ("Hotel Name", "Location", "Phone"))
    print("-" * 90)

    existing_leads = load_leads()
    existing_names = {l.get("hotel_name", "").lower() for l in existing_leads}
    added = 0

    for idx, r in enumerate(results, 1):
        if isinstance(r, dict) and "hotel_name" in r:
            name = r["hotel_name"]
            phone = r.get("phone", "") or "Not listed"
            web = r.get("website", "") or "[NO WEBSITE]"
            print("%-36s | %-16s | %-22s | %s" % (name[:36], args.city[:16], phone[:22], web))

            if args.add and name.lower() not in existing_names:
                lead_id = "lead-%03d" % (len(existing_leads) + 1)
                new_lead = {
                    "id": lead_id,
                    "hotel_name": name,
                    "city": args.city,
                    "contact_name": "Hotel Manager / Owner",
                    "email": r.get("email", ""),
                    "phone": r.get("phone", ""),
                    "website": r.get("website", ""),
                    "current_web_status": r.get("current_web_status", "No website found"),
                    "audit_notes": r.get("audit_notes", f"No website detected in {args.city}. Needs direct booking engine & review showcase."),
                    "outreach_status": "identified",
                    "date_added": datetime.now().strftime("%Y-%m-%d"),
                    "last_action": datetime.now().strftime("%Y-%m-%d"),
                    "follow_up_date": datetime.now().strftime("%Y-%m-%d"),
                    "emails_sent": 0,
                    "assumed_commission": 0.18
                }
                existing_leads.append(new_lead)
                existing_names.add(name.lower())
                added += 1

    if args.add:
        save_leads(existing_leads)
        print(f"\n[+] Added {added} new leads into {LEADS_FILE}")
    else:
        print("\nTip: Re-run with '--add' flag to automatically import these leads into your CRM pipeline.")


def cmd_list(args):
    leads = load_leads()
    if args.status:
        leads = [l for l in leads if l.get("outreach_status") == args.status]

    print(f"\nTotal Leads: {len(leads)}")
    print("%-10s | %-28s | %-16s | %-12s | %-22s | %s" % ("ID", "Hotel", "City", "Status", "Email", "Phone"))
    print("-" * 105)
    for l in leads:
        print("%-10s | %-28s | %-16s | %-12s | %-22s | %s" % (
            l.get("id", ""),
            l.get("hotel_name", "")[:28],
            l.get("city", "")[:16],
            l.get("outreach_status", "")[:12],
            (l.get("email") or "No email")[:22],
            (l.get("phone") or "No phone")[:18]
        ))


def cmd_pitch(args):
    script = os.path.join(SCRIPTS_DIR, "outreach_sender.py")
    cmd = [sys.executable, script]
    if args.id:
        cmd.extend(["--id", args.id])
    if args.commit:
        cmd.append("--commit")
    else:
        cmd.append("--dry-run")
    subprocess.run(cmd)


def cmd_reply(args):
    script = os.path.join(SCRIPTS_DIR, "deal_closer.py")
    cmd = [sys.executable, script, "reply", "--id", args.id]
    if args.intent:
        cmd.extend(["--intent", args.intent])
    if args.text:
        cmd.extend(["--text", args.text])
    subprocess.run(cmd)


def cmd_contract(args):
    script = os.path.join(SCRIPTS_DIR, "deal_closer.py")
    cmd = [sys.executable, script, "contract", "--id", args.id, "--price", str(args.price), "--currency", args.currency]
    if args.out:
        cmd.extend(["--out", args.out])
    subprocess.run(cmd)


def cmd_dashboard(args):
    import http.server, socketserver
    port = args.port
    # Copy latest data to goa_leads_site/leads.json so dashboard stays in sync
    site_dir = os.path.join(ROOT_DIR, "goa_leads_site")
    leads = load_leads()
    site_leads_file = os.path.join(site_dir, "leads.json")
    with open(site_leads_file, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)

    os.chdir(site_dir)
    handler = http.server.SimpleHTTPRequestHandler
    print(f"[*] Starting Hotel CRM & Deal Closer Dashboard on http://localhost:{port} ...")
    try:
        webbrowser.open(f"http://localhost:{port}")
    except Exception:
        pass

    with socketserver.TCPServer(("", port), handler) as httpd:
        try:
            print(f"[*] Dashboard is LIVE at http://localhost:{port} (Press Ctrl+C to stop)")
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nDashboard stopped.")


def cmd_auto(args):
    """
    Full Autonomous Pipeline:
      1. Discover hotels without websites in target cities.
      2. Auto-audit and qualify leads.
      3. Auto-generate cold pitches (direct booking + customer review showcase).
      4. Auto-send emails if --commit is specified, or queue safely.
      5. Auto-generate closing replies and ready-to-sign contracts for replied leads.
      6. Sync data to the live CRM Dashboard.
    """
    from scripts.prospect_finder import find_osm
    from scripts.outreach_sender import render as render_pitch, send_one, load_config
    from scripts.deal_closer import generate_cooperative_reply, generate_contract

    cities = [c.strip() for c in args.cities.split(",") if c.strip()]
    print("\n" + "=" * 60)
    print("🚀 STARTING HOTEL LEAD GEN & DEAL CLOSER AUTONOMOUS PIPELINE")
    print("=" * 60)

    # 1. DISCOVERY & AUDIT
    leads = load_leads()
    existing_names = {l.get("hotel_name", "").lower() for l in leads}
    new_leads_added = 0

    print(f"\n[Phase 1] Auto-Discovering hotels lacking websites across: {', '.join(cities)}...")
    for city in cities:
        print(f"  -> Scanning {city}...")
        results = find_osm(city, limit=args.limit_per_city)
        for r in results:
            if isinstance(r, dict) and "hotel_name" in r:
                name = r["hotel_name"]
                if name.lower() not in existing_names:
                    lead_id = "lead-%03d" % (len(leads) + 1)
                    new_lead = {
                        "id": lead_id,
                        "hotel_name": name,
                        "city": city,
                        "contact_name": "Hotel Manager / Owner",
                        "email": r.get("email", ""),
                        "phone": r.get("phone", ""),
                        "website": r.get("website", ""),
                        "current_web_status": r.get("current_web_status", "No website found"),
                        "audit_notes": r.get("audit_notes", f"No website detected in {city}. Needs direct booking engine & review showcase."),
                        "outreach_status": "identified",
                        "date_added": datetime.now().strftime("%Y-%m-%d"),
                        "last_action": datetime.now().strftime("%Y-%m-%d"),
                        "follow_up_date": datetime.now().strftime("%Y-%m-%d"),
                        "emails_sent": 0,
                        "assumed_commission": 0.18
                    }
                    leads.append(new_lead)
                    existing_names.add(name.lower())
                    new_leads_added += 1

    save_leads(leads)
    print(f"  [✓] Auto-discovery complete: {new_leads_added} new hotels added to pipeline (Total: {len(leads)}).")

    # 2. OUTREACH DISPATCH / GENERATION
    cfg = load_config()
    print(f"\n[Phase 2] Auto-Pitching Qualified Leads (Direct Booking & Review Engine)...")
    pitches_generated = 0
    today = datetime.now().strftime("%Y-%m-%d")

    for l in leads:
        if l.get("outreach_status") == "identified":
            subject, body = render_pitch(l, cfg)
            pitches_generated += 1
            if args.commit and l.get("email"):
                print(f"  -> Sending live email to: {l['hotel_name']} <{l['email']}>")
                send_one(l, subject, body, cfg, dry=False, today=today)
            else:
                l["prepared_subject"] = subject
                l["prepared_body"] = body

    save_leads(leads)
    mode_str = "sent via SMTP" if args.commit else "prepared & queued (dry-run)"
    print(f"  [✓] Processed {pitches_generated} pitches ({mode_str}).")

    # 3. AUTO-CLOSER & CONTRACT GENERATION FOR REPLIED LEADS
    print(f"\n[Phase 3] Auto-Processing Inbound Replies & Generating Contracts...")
    contracts_dir = os.path.join(ROOT_DIR, "contracts")
    os.makedirs(contracts_dir, exist_ok=True)
    replies_processed = 0

    for l in leads:
        if l.get("outreach_status") in ("replied", "proposal"):
            replies_processed += 1
            # Generate winning negotiation reply
            subj, reply_body = generate_cooperative_reply(l, intent="price", cfg=cfg)
            # Generate formal contract agreement
            contract_text = generate_contract(l, price=args.contract_price, currency=args.currency, cfg=cfg)
            filename = f"Contract_{l['id']}_{l['hotel_name'].replace(' ', '_')}.md"
            contract_path = os.path.join(contracts_dir, filename)
            with open(contract_path, "w", encoding="utf-8") as cf:
                cf.write(contract_text)
            print(f"  [✓] Generated closing reply & agreement for {l['hotel_name']} -> {filename}")

    # 4. SYNC TO CRM DASHBOARD
    site_dir = os.path.join(ROOT_DIR, "goa_leads_site")
    site_leads_file = os.path.join(site_dir, "leads.json")
    with open(site_leads_file, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)
    print(f"\n[Phase 4] [✓] Synced CRM Dashboard with latest {len(leads)} leads.")

    print("\n" + "=" * 60)
    print("✨ AUTOMATION CYCLE COMPLETED SUCCESSFULLY")
    print(f"   • Total Active Leads    : {len(leads)}")
    print(f"   • New Hotels Found      : {new_leads_added}")
    print(f"   • Outreach Pitches      : {pitches_generated}")
    print(f"   • Agreements Generated  : {replies_processed} (saved in /contracts/)")
    print("   • Live Web CRM          : Run 'python hotel_agent.py dashboard' to view")
    print("=" * 60 + "\n")


def main():
    p = argparse.ArgumentParser(
        description="Hotel Lead Generation & Contract Closer Agent",
        formatter_class=argparse.RawTextHelpFormatter
    )
    sub = p.add_subparsers(dest="action", required=True)

    # Auto
    sa = sub.add_parser("auto", help="Run full end-to-end automation cycle on autopilot")
    sa.add_argument("--cities", default="Goa,Panjim,Calangute", help="Comma-separated cities to scan")
    sa.add_argument("--limit-per-city", type=int, default=5, help="Hotels to discover per city")
    sa.add_argument("--contract-price", type=float, default=28000.0, help="Default contract fee")
    sa.add_argument("--currency", default="INR", help="Currency code (INR, USD, EUR)")
    sa.add_argument("--commit", action="store_true", help="Send live emails via SMTP (default is preview)")
    sa.set_defaults(func=cmd_auto)

    # Find
    sf = sub.add_parser("find", help="Find hotels without websites in a city/region")
    sf.add_argument("--city", required=True, help="City or area name (e.g. 'Goa', 'Miami', 'Manali')")
    sf.add_argument("--limit", type=int, default=10, help="Max results to fetch")
    sf.add_argument("--add", action="store_true", help="Add discovered hotels into lead database")
    sf.set_defaults(func=cmd_find)

    # List
    sl = sub.add_parser("list", help="List active hotel leads")
    sl.add_argument("--status", choices=["identified", "emailed", "replied", "proposal", "closed_won", "lost"], help="Filter by status")
    sl.set_defaults(func=cmd_list)

    # Pitch
    sp = sub.add_parser("pitch", help="Draft or send cold email with booking & reviews pitch")
    sp.add_argument("--id", help="Lead ID (optional, defaults to all)")
    sp.add_argument("--commit", action="store_true", help="Send live via SMTP (default is preview dry-run)")
    sp.set_defaults(func=cmd_pitch)

    # Reply
    sr = sub.add_parser("reply", help="Generate objection-handling response when hotel replies")
    sr.add_argument("--id", required=True, help="Lead ID")
    sr.add_argument("--intent", choices=["price", "ota_objection", "demo_interest", "no_need", "contract_ready"], help="Specific intent")
    sr.add_argument("--text", help="Client's incoming message text")
    sr.set_defaults(func=cmd_reply)

    # Contract
    sc = sub.add_parser("contract", help="Generate website development contract for hotel")
    sc.add_argument("--id", required=True, help="Lead ID")
    sc.add_argument("--price", type=float, default=25000.0, help="Total contract price (default: 25000)")
    sc.add_argument("--currency", default="INR", help="Currency code (e.g. INR, USD, EUR)")
    sc.add_argument("--out", help="Output file path (e.g. contract.md)")
    sc.set_defaults(func=cmd_contract)

    # Dashboard
    sd = sub.add_parser("dashboard", help="Open local CRM and deal closer dashboard")
    sd.add_argument("--port", type=int, default=8080, help="Port to run web dashboard")
    sd.set_defaults(func=cmd_dashboard)

    # Add scripts dir to python path
    sys.path.insert(0, SKILL_DIR)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
