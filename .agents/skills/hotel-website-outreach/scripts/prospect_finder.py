#!/usr/bin/env python3
"""
prospect_finder.py - Prospect discovery + website audit.

Two modes:
  * audit  <url>       Check a single prospect website for the three qualification
                       signals used by the skill:
                         - HTTP (insecure) vs HTTPS
                         - No website / unreachable / parked
                         - Presence of a direct booking engine vs redirect to
                           Booking.com/Expedia/Agoda/etc. (OTA commission loss)
                       Prints a JSON qualification verdict you can pipe into
                       lead_manager.add --status-note.

  * find  <city/area>  (Optional helper) Runs web searches for candidate hotels
                       via DuckDuckGo's HTML endpoint and prints candidate names
                       + domains for you to audit. Best-effort, no API key.

Stdlib only (urllib). "--offline" skips network and audits a provided snapshot.

Usage:
  python prospect_finder.py audit https://sunsetcoveresort.com
  python prospect_finder.py audit https://sunsetcoveresort.com --offline "no booking engine; redirects to booking.com"
  python prospect_finder.py find "boutique hotels Margate UK"
"""
import argparse, json, re, sys, urllib.request, urllib.parse

OTA_MARKERS = ["booking.com", "expedia", "agoda", "hotels.com", "tripadvisor",
               "airbnb", "hotelbeds", "amadeus", "sabre"]
TIMEOUT = 12
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; HotelLeadAudit/1.0)"}


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    resp = urllib.request.urlopen(req, timeout=TIMEOUT)
    final_url = resp.geturl()
    html = resp.read(120000).decode("utf-8", errors="ignore").lower()
    return resp.status, final_url, html


def audit_url(url):
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    try:
        status, final_url, html = fetch(url)
    except Exception as e:
        return {
            "url": url, "reachable": False, "error": str(e),
            "qualified": True,
            "reason": "Website unreachable / parked / offline.",
            "ota_redirect": None, "secure": None,
        }

    secure = url.startswith("https://")
    ota_found = [m for m in OTA_MARKERS if m in final_url or m in html]

    # Down-rank: reachable with booking capability and secure = lower priority.
    qualified = (not secure) or (not ota_found) or (status != 200 and not ota_found)
    reasons = []
    if not secure:
        reasons.append("Served over insecure HTTP (no SSL).")
    if ota_found:
        reasons.append("Booking redirects to / links to OTA(s): %s — losing ~15-25%% commission." % ", ".join(sorted(set(ota_found[:4]))))
    if not ota_found:
        reasons.append("No obvious direct booking engine found (may rely on calls/OTAs).")

    return {
        "url": url, "reachable": True, "http_status": status,
        "final_url": final_url, "secure": secure,
        "ota_redirect": sorted(set(ota_found)) if ota_found else None,
        "qualified": qualified, "reason": " ".join(reasons),
    }


def find_candidates(area):
    q = urllib.parse.quote_plus('"%s" hotel -site:booking.com' % area)
    url = "https://html.duckduckgo.com/html/?q=" + q
    try:
        _, _, html = fetch(url)
    except Exception as e:
        sys.exit("Search failed: %s (use audit mode directly)" % e)
    results = re.findall(r'href="([^"]+)"[^>]*class="result__a"', html)
    titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', html, re.S)
    seen = set()
    out = []
    for href, title in zip(results, titles):
        if "duckduckgo" in href or "uddg=" not in href:
            continue
        target = urllib.parse.unquote(re.search(r"uddg=([^&]+)", href).group(1))
        key = target.split("/")[2] if target.startswith(("http://", "https://")) else target
        if key in seen:
            continue
        seen.add(key)
        clean = re.sub(r"<[^>]+>", "", title).strip()
        out.append({"title": clean, "domain": key})
        if len(out) >= 10:
            break
    return out


def find_osm(area, limit=20):
    """
    Search OpenStreetMap Overpass API for hospitality properties in `area`
    and filter for those WITHOUT an official website or relying strictly on OTAs/social.
    """
    import urllib.error
    # 1. Geocode area using Nominatim to get bounding box or osm_id
    nom_url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({
        "q": area, "format": "json", "limit": 1
    })
    headers = {"User-Agent": "HotelLeadGenerationAgent/1.0 (contact@hotelagent.local)"}
    try:
        req = urllib.request.Request(nom_url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            geo_data = json.loads(resp.read().decode("utf-8"))
            if not geo_data:
                return find_candidates(area)
            bbox = geo_data[0].get("boundingbox") # [minlat, maxlat, minlon, maxlon]
    except Exception:
        return find_candidates(area)

    if not bbox or len(bbox) < 4:
        return find_candidates(area)

    south, north, west, east = bbox[0], bbox[1], bbox[2], bbox[3]
    # 2. Overpass query in bounding box
    query = f"""[out:json][timeout:25];
(
  node["tourism"~"hotel|guest_house|motel|chalet|hostel"]({south},{west},{north},{east});
  way["tourism"~"hotel|guest_house|motel|chalet|hostel"]({south},{west},{north},{east});
);
out tags center {limit * 3};"""

    op_url = "https://overpass-api.de/api/interpreter"
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    try:
        req = urllib.request.Request(op_url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            res = json.loads(resp.read().decode("utf-8"))
    except Exception:
        # Fallback to search if Overpass is temporarily unavailable
        return find_candidates(area)

    elements = res.get("elements", [])
    leads = []
    seen = set()

    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name or name in seen:
            continue
        seen.add(name)

        website = tags.get("website") or tags.get("contact:website") or ""
        phone = tags.get("phone") or tags.get("contact:phone") or ""
        email = tags.get("email") or tags.get("contact:email") or ""
        tourism_type = tags.get("tourism", "hotel").replace("_", " ").title()

        # Check qualification: No website or website is an OTA/Facebook
        is_no_website = not website
        is_ota_site = any(m in website.lower() for m in OTA_MARKERS) if website else False
        is_social_only = ("facebook.com" in website.lower() or "instagram.com" in website.lower()) if website else False

        if is_no_website or is_ota_site or is_social_only:
            status_desc = "No official website found on Maps/OSM" if is_no_website else ("Social page only: " + website if is_social_only else "Redirects to OTA: " + website)
            leads.append({
                "hotel_name": name,
                "city": area,
                "tourism_type": tourism_type,
                "contact_name": "Hotel Manager / Owner",
                "email": email,
                "phone": phone,
                "website": website,
                "current_web_status": status_desc,
                "audit_notes": f"{tourism_type} in {area}. {status_desc}. Zero-commission booking & review showcase needed.",
                "qualified": True,
                "outreach_status": "identified"
            })
            if len(leads) >= limit:
                break

    return leads if leads else find_candidates(area)


def main():
    p = argparse.ArgumentParser(description="Hotel prospect audit / finder")
    sub = p.add_subparsers(dest="cmd", required=True)

    sa = sub.add_parser("audit"); sa.add_argument("url"); sa.add_argument("--offline", help="Offline audit: pass a status note string"); sa.set_defaults(func=lambda a: audit_url(a.url) if not a.offline else {
        "url": a.url, "reachable": "offline", "qualified": True, "reason": a.offline})
    sf = sub.add_parser("find")
    sf.add_argument("area")
    sf.add_argument("--limit", type=int, default=15, help="Max results")
    sf.add_argument("--source", choices=["osm", "web"], default="osm", help="Discovery source")
    sf.set_defaults(func=lambda a: find_osm(a.area, a.limit) if a.source == "osm" else find_candidates(a.area))

    args = p.parse_args()
    result = args.func(args)
    if isinstance(result, list):
        for r in result:
            if isinstance(r, dict) and "hotel_name" in r:
                print("%-36s | %-16s | Phone: %-15s | Web: %s" % (
                    r["hotel_name"][:36], r.get("city", "")[:16], r.get("phone", "N/A")[:15], r.get("website") or "NO WEBSITE"
                ))
            elif isinstance(r, dict) and "title" in r:
                print("%-45s %s" % (r["title"][:45], r["domain"]))
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()