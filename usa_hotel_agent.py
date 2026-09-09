#!/usr/bin/env python3
"""USA hotel lead generator - reuses Indian agent logic for USA cities"""
import csv, json, os, sys, urllib.parse, urllib.request
from datetime import datetime
HERMES_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_OUTPUT = os.path.join(HERMES_DIR, "indian_hotel_leads.csv")  # same CSV, USA city tag
sys.path.insert(0, HERMES_DIR)
try:
    from telegram_notifier import send_message, load_config
except Exception:
    send_message = load_config = None
USA_CITIES = ["New York","Los Angeles","Miami","Las Vegas","Orlando","Chicago","San Francisco","Austin","New Orleans","Seattle","Boston","Denver"]

def find_usa_hotels(city, limit=15):
    headers={"User-Agent":"HermesUSA/1.0"}
    nom_url="https://nominatim.openstreetmap.org/search?"+urllib.parse.urlencode({"q":f"{city}, USA","format":"json","limit":1})
    try:
        req=urllib.request.Request(nom_url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            geo=json.loads(resp.read().decode())
            if not geo: return []
            bbox=geo[0].get("boundingbox")
    except: return []
    south,north,west,east=bbox[0],bbox[1],bbox[2],bbox[3]
    fetch_n=min(limit*8,100)
    query=f"""[out:json][timeout:45];
(
  node["tourism"~"hotel|guest_house|motel|chalet|hostel|homestay|apartment"]({south},{west},{north},{east});
  way["tourism"~"hotel|guest_house|motel|chalet|hostel|homestay|apartment"]({south},{west},{north},{east});
  node["amenity"="hotel"]({south},{west},{north},{east});
  way["amenity"="hotel"]({south},{west},{north},{east});
);
out tags center {fetch_n};"""
    try:
        data=urllib.parse.urlencode({"data":query}).encode()
        req=urllib.request.Request("https://overpass-api.de/api/interpreter", data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=45) as resp:
            res=json.loads(resp.read().decode())
    except: return []
    leads=[]; seen=set()
    for el in res.get("elements",[]):
        tags=el.get("tags",{}); name=tags.get("name")
        if not name or name in seen: continue
        seen.add(name)
        web=tags.get("website") or tags.get("contact:website") or ""
        phone=tags.get("phone") or tags.get("contact:phone") or ""
        email=tags.get("email") or tags.get("contact:email") or ""
        ota_markers=["booking.com","expedia","agoda","airbnb"]
        is_ota=any(m in web.lower() for m in ota_markers) if web else False
        if not web or is_ota:
            leads.append({"hotel_name":name,"city":city,"phone":phone,"email":email,"website":web,"status":"No website (OTA dependent)","audit_notes":f"Independent hotel in {city}, USA. No direct booking website. Losing 15-25% commission to Booking.com/Expedia."})
            if len(leads)>=limit: break
    return leads

def save_usa_leads(all_leads, city=None):
    FIELDNAMES=["id","hotel_name","city","phone","email","website","status","date_discovered","audit_notes"]
    existing=[]
    if os.path.exists(CSV_OUTPUT):
        with open(CSV_OUTPUT, encoding="utf-8", errors="ignore") as f:
            reader=csv.DictReader(f)
            for r in reader:
                if r.get("id") and r["id"]!="id": existing.append(r)
    seen_names=set((r["hotel_name"].lower(), r["city"].lower()) for r in existing)
    max_id=0
    for r in existing:
        try: max_id=max(max_id, int(r["id"].split("-")[-1]))
        except: pass
    added=0
    for lead in all_leads:
        key=(lead["hotel_name"].lower(), lead["city"].lower())
        if key in seen_names: continue
        seen_names.add(key)
        max_id+=1
        lid=f"us-lead-{max_id:03d}" if lead["city"] in USA_CITIES else f"in-lead-{max_id:03d}"
        existing.append({"id":lid,"hotel_name":lead["hotel_name"],"city":lead["city"],"phone":lead["phone"],"email":lead["email"],"website":lead["website"],"status":lead["status"],"date_discovered":datetime.now().strftime("%Y-%m-%d"),"audit_notes":lead["audit_notes"]})
        added+=1
    with open(CSV_OUTPUT,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=FIELDNAMES); w.writeheader(); w.writerows(existing)

    # Telegram notification
    if send_message and load_config:
        try:
            cfg = load_config()
            bot_token = cfg.get('bot_token')
            chat_id = cfg.get('chat_id')
            if bot_token and chat_id:
                city_label = city or "USA"
                lines = [f"🧭 <b>USA Leads Found</b> — {city_label}"]
                lines.append(f"📊 Found: {len(all_leads)} | New: {added} | Total DB: {len(existing)}")
                if all_leads:
                    lines.append("\n<b>Top leads:</b>")
                    for lead in all_leads[:8]:
                        name = lead.get('hotel_name','')
                        web = lead.get('website','') or 'no website'
                        lines.append(f"• {name} | {web}")
                text = "\n".join(lines)
                send_message(bot_token, chat_id, text)
        except Exception:
            pass

    return added, len(existing)

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--city", default=None)
    p.add_argument("--limit", type=int, default=15)
    p.add_argument("--all", action="store_true", help="scan all USA cities")
    args=p.parse_args()
    if args.all:
        total_added=0
        for city in USA_CITIES:
            print(f"[→] Scanning {city}...")
            leads=find_usa_hotels(city, limit=args.limit)
            added,total=save_usa_leads(leads)
            print(f"[✓] {city}: {len(leads)} found, {added} new, total {total}")
        print(f"Done. Total added {total_added}")
    elif args.city:
        leads=find_usa_hotels(args.city, limit=args.limit)
        added,total=save_usa_leads(leads)
        print(f"{args.city}: {len(leads)} found, {added} new -> total {total}")
        for l in leads[:5]: print(f"  - {l['hotel_name']}")
    else:
        print("Use --city 'New York' or --all")
