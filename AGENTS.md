# Hermes Hotel Outreach Agent - Project Guide

## Project Overview

This is an autonomous hotel lead-generation and cold-outreach system running on the Hermes Agent platform. It discovers independent hotels, guesthouses, and resorts in India (primarily Goa) that lack websites or direct booking engines, then pitches them custom sites with zero-commission direct booking & review showcase systems.

## Architecture

```
hermes/                                 # Project root
├── hotel_agent.py                      # Master orchestrator (CLI)
├── indian_hotel_agent.py               # India-specific discovery + INR outreach
├── goa_leads_site/index.html           # Interactive CRM dashboard
├── Contracts/                          # Generated agreements
├── indian_hotel_leads.csv              # Lead database (CSV)
├── indian_hotel_leads.xlsx             # Lead database (Excel export)
├── .agents/skills/hotel-website-outreach/   # Base skill scripts
│   ├── scripts/
│   │   ├── prospect_finder.py          # OSM/Nominatim hotel discovery + site audit
│   │   ├── outreach_sender.py        # Cold email sender (SMTP, anti-spam)
│   │   ├── deal_closer.py            # Reply classifier + contract generator
│   │   ├── lead_manager.py           # Lead pipeline tracker (JSON)
│   │   └── roi_calculator.py         # Commission loss / ROI calculator
│   └── data/
│       ├── hotel_leads.json          # JSON lead DB
│       ├── config.json               # SMTP config + pitch settings
│       └── hotel_leads.json          # JSON lead DB
└── .kilo/command/                      # Kilo command shortcuts
```

## Key Workflows

### Discovery
```bash
python indian_hotel_agent.py --city "Goa" --limit 10
python hotel_agent.py find --city "Goa" --limit 10 --add
```

### Pitch (preview before sending)
```bash
python hotel_agent.py pitch --id lead-001          # dry-run
python hotel_agent.py pitch --id lead-001 --commit  # live SMTP send
```

### Closing
```bash
python hotel_agent.py reply --id lead-002 --intent price
python hotel_agent.py contract --id lead-003 --price 28000 --currency INR --out contract.md
```

### CRM Dashboard
```bash
python hotel_agent.py dashboard --port 8080
```

### Full Auto Pipeline
```bash
python hotel_agent.py auto --cities "Goa,Manali,Jaipur" --commit
```

## Scheduled Jobs (Hermes Cron)
- `hotel-pipeline-daily-due` — Daily at 9:00 AM
- `daily_hotel_discovery` — Every 24h, discovers Goa hotels
- `weekly_hotel_contract_gen` — Every 7 days, generates contracts for replied leads

## Email Configuration
- SMTP: Gmail (smtp.gmail.com:587)
- Sender: ahmadbkj92@gmail.com ("Ahmad Raza")
- Daily send limit: 30 (warmup cap: 20)
- Unsubscribe link injected in every email

## Testing
```bash
python -m py_compile hotel_agent.py indian_hotel_agent.py .agents/skills/hotel-website-outreach/scripts/*.py
```
