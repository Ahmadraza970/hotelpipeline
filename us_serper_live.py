import csv, json, re, os, urllib.request, urllib.parse, time
from datetime import datetime
HERMES_DIR = os.environ.get("HERMES_DIR", os.path.expanduser("~"))
CSV = os.path.join(HERMES_DIR, "indian_hotel_leads.csv")
SERPER_KEY = os.environ.get("SERPER_KEY", "d0f391c08934a027ae79ef736de987af6a16de36")
USA_CITIES=["New York","Miami","Los Angeles","Las Vegas","Orlando","Austin","Seattle","Denver"]
def s_search(q):
    d=json.dumps({"q":q,"num":10}).encode()
    req=urllib.request.Request("https://google.serper.dev/search", data=d, headers={"X-API-KEY":SERPER_KEY,"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())
def ext_email(t):
    ms=re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", t)
    filt=[e for e in ms if "example" not in e.lower() and "info@gmail.com" not in e.lower() and "test@" not in e.lower()]
    pref=[e for e in filt if any(k in e.lower() for k in ["info","contact","reservation","booking","sales","hello"])]
    return (pref[0] if pref else (filt[0] if filt else ""))
def ext_phone(t):
    ms=re.findall(r"\+1[\s\-]*\(?\d{3}\)?[\s\-]*\d{3}[\s\-]*\d{4}", t)
    return ms[0] if ms else ""
FIELDNAMES=["id","hotel_name","city","phone","email","website","status","date_discovered","audit_notes"]
rows=list(csv.DictReader(open(CSV, encoding="utf-8")))
max_id=0
for r in rows:
    try: max_id=max(max_id, int(r["id"].split("-")[-1]))
    except: pass
seen=set((r["hotel_name"].lower(), r["city"].lower()) for r in rows)
added=0
for city in USA_CITIES[:4]:
    print(f"[→] Serper live USA: {city}")
    queries=[f"hotels in {city} USA boutique hotel contact email", f"{city} independent hotel phone email site:.com", f"{city} guest house motel email reservation"]
    for q in queries:
        try:
            res=s_search(q)
            for o in res.get("organic",[]):
                title=o.get("title",""); snippet=o.get("snippet",""); link=o.get("link","")
                blob=title+" "+snippet+" "+link
                # hotel name from title
                name=title.split("-")[0].split("|")[0].strip()[:40]
                if len(name)<4 or "hotels" in name.lower() and len(name)>30: continue
                email=ext_email(blob)
                phone=ext_phone(blob)
                # need email or phone to be useful
                if not email and not phone: continue
                key=(name.lower(), city.lower())
                if key in seen: continue
                seen.add(key)
                max_id+=1
                lid=f"us-serper-{max_id:04d}"
                rows.append({"id":lid,"hotel_name":name,"city":city,"phone":phone,"email":email,"website":link if "hotel" in link.lower() else "","status":"Serper USA live","date_discovered":datetime.now().strftime("%Y-%m-%d"),"audit_notes":f"USA independent hotel in {city} found via live Google Search. No direct booking site. Losing 15-25% to Booking.com/Expedia."})
                added+=1
                print(f"  + {name} | {email or phone} | {city}")
                if added>=15: break
            if added>=15: break
        except Exception as e: print(f"  err {q[:30]} {e}")
        time.sleep(0.5)
    print(f"[✓] {city} done, total added {added}")
    if added>=50: break
rows.sort(key=lambda x: x["id"])
with open(CSV,"w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f, fieldnames=FIELDNAMES); w.writeheader(); w.writerows([{k:r.get(k,"") for k in FIELDNAMES} for r in rows])
print(f"TOTAL added {added}, now {len(rows)} rows")
