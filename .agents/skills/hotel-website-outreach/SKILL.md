---
name: hotel-website-outreach
description: Automates discovering hotels without proper websites or direct booking engines, generating targeted cold email pitches highlighting commission savings and modern web design, and handling client replies.
---

# Hotel Website & Direct Booking System Automation

This skill provides an automated workflow to identify hotels, guesthouses, and boutique lodges that lack a proper website or direct booking system, pitch custom web development solutions, and manage client engagement when they respond.

---

## Workflow Overview

```
 ┌───────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
 │ 1. Prospecting        │ ───► │ 2. Audit & Verification │ ───► │ 3. Personalized Pitch   │
 │ Find hotels via Maps/ │      │ Check site status & OTA │      │ Draft & send tailored   │
 │ web search / OTAs     │      │ commission dependency   │      │ email proposal          │
 └───────────────────────┘      └─────────────────────────┘      └─────────────────────────┘
                                                                              │
                                                                              ▼
 ┌───────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
 │ 6. Onboarding         │ ◄─── │ 5. Proposal & Demo      │ ◄─── │ 4. Response Handling    │
 │ Collect assets, set   │      │ Present interactive demo│      │ Nurture replies, answer │
 │ up booking & launch   │      │ & booking calculation   │      │ questions, address OTAs │
 └───────────────────────┘      └─────────────────────────┘      └─────────────────────────┘
```

---

## Phase 1: Prospecting & Lead Finding

### Search Strategies
Run localized web searches for independent hospitality businesses (boutique hotels, guesthouses, B&Bs, resorts, lodges):

- Search Queries:
  - `"hotels in [City/Region]" -"booking.com" -"expedia.com"`
  - `"boutique hotel [City/Region] contact email"`
  - `"guesthouse [City/Region] no website"`
  - `"bed and breakfast [City/Region] direct booking"`

### Lead Qualification Criteria
Check each prospect against the following criteria:

1. **No Official Website**: Only listed on Google Business Profile, Facebook page, or OTA directories (Booking.com, Expedia, TripAdvisor).
2. **Outdated / Non-Responsive Site**: Website is HTTP (insecure), not mobile-friendly, or uses obsolete formatting.
3. **No Direct Booking Engine**: Website has no real-time reservation system (only "Call us to book" or redirects to Booking.com where they lose 15–25% commission per room).

---

## Phase 2: Audit & Data Collection

Log prospect details into a CSV/JSON file (`hotel_leads.json`):

```json
[
  {
    "id": "lead-001",
    "hotel_name": "Sunset Cove Resort",
    "city": "Miami, FL",
    "contact_name": "Hotel Manager / Owner",
    "email": "info@sunsetcoveresort.com",
    "phone": "+1-305-555-0199",
    "current_web_status": "No direct booking engine; redirects to Booking.com",
    "audit_notes": "Losing ~18% commission on every reservation; mobile view broken",
    "outreach_status": "Identified",
    "date_added": "2026-08-26"
  }
]
```

---

## Phase 3: Personalized Outreach Emails

### Email Template 1: Direct Commission Savings Pitch (Recommended)

**Subject**: Direct booking system for {{hotel_name}} (Stop paying 18% OTA fees)

**Body**:
> Hi {{contact_name}},
>
> I came across **{{hotel_name}}** while researching top-rated places to stay in {{city}}. Your property looks fantastic, but I noticed guests currently have to rely on third-party sites like Booking.com/Expedia to reserve a room.
>
> Every time a guest books through an OTA, you're paying **15% to 25% in commissions**. On a $150/night room booked for 3 nights, that’s up to **$80+ lost per reservation**.
>
> We build custom, fast, mobile-friendly websites for boutique hotels equipped with an **instant direct booking engine**:
>
> - 🏨 **Zero-Commission Direct Bookings**: Accept credit cards and instant reservations on your own website.
> - 📱 **Mobile Optimized**: 70%+ of travelers book on smartphones — your site will look stunning on all devices.
> - 📅 **Channel Manager Sync**: Automatically sync calendar availability with Airbnb, Booking.com, and Google Hotels to prevent double-bookings.
> - ⚡ **Fast Setup**: Turnkey delivery in under 10 days with complete staff walkthrough.
>
> Would you be open to a quick 5-minute preview of a custom demo site we designed for {{hotel_name}}?
>
> Best regards,  
> **[Your Name / Agency Name]**  
> [Your Portfolio Link / Phone Number]

---

### Email Template 2: Website Modernization & Direct Booking Pitch

**Subject**: Modernizing {{hotel_name}}’s web presence & booking system

**Body**:
> Hello {{contact_name}},
>
> I was looking over {{hotel_name}}'s current web listing in {{city}}. You have great traveler reviews, but your web presence doesn't do justice to the quality of your property.
>
> Today’s travelers expect a seamless online booking experience. Without a fast, modern website and direct reservation system:
> 1. Prospective guests bounce to competitors with easier mobile booking.
> 2. You lose thousands monthly in OTA commission fees.
>
> We specialize in crafting high-converting hotel websites featuring direct reservation systems, virtual room walkthroughs, and multi-language support.
>
> I’d love to show you a quick mockup tailored for {{hotel_name}}. Are you available for a brief chat this week?
>
> Warm regards,  
> **[Your Name / Agency Name]**

---

## Phase 4: Reply Handling & Cooperation Workflow

When a hotel owner or manager replies, follow this stage-by-stage guide:

### Scenario A: "How much does it cost?"
**Response Strategy**: Provide clear tiered pricing and emphasize Return on Investment (ROI).

- **Sample Reply**:
  > Hi {{contact_name}},
  > 
  > Thanks for getting back to me! Our hotel packages start at **$X,XXX** (one-time) or **$XX/month** which includes:
  > - Complete modern website design & photo showcase
  > - Commission-free direct booking engine & payment gateway
  > - Calendar sync (iCal / OTA channel manager)
  > - Mobile responsiveness & SEO optimization
  > 
  > Most of our clients recoup the full investment within 30 to 60 days simply from direct booking commission savings.
  > 
  > Can we schedule a brief 10-minute Zoom call or demo this [Day] at [Time]?

---

### Scenario B: "We already get enough bookings from Booking.com / Airbnb."
**Response Strategy**: Frame direct bookings not as replacing OTAs, but as capturing repeat guests and high-margin direct traffic.

- **Sample Reply**:
  > Hi {{contact_name}},
  > 
  > That’s great to hear that OTAs are driving steady volume for {{hotel_name}}!
  > 
  > Our goal isn't to replace your OTA listings, but to help you **turn repeat guests into 100% direct profit bookings**. When a returning guest wants to book again, having your own direct booking site saves you 15-20% on every stay they make.
  > 
  > I'd be glad to send over a 2-minute video walkthrough of how our direct booking engine works alongside your existing OTA channels. Would that be helpful?

---

### Scenario C: "Yes, show me a demo / I'm interested!"
**Action Steps**:
1. Create a rapid mock-up preview (using a pre-built hotel template customized with their hotel name, logo, and room images).
2. Schedule a short discovery call / demo presentation.
3. Prepare a tailored proposal outlining scope, timeline (e.g. 7-14 days), and deliverables.

---

## Lead Pipeline Tracking Table

All active prospects are tracked programmatically in **`data/hotel_leads.json`** by the
pipeline tracker. Run commands from this skill's `scripts/` directory (Python 3.10+,
standard library only — no installs needed).

```bash
# Add a NEW lead (from prospecting or an audit)
python scripts/lead_manager.py add --name "Sunset Cove Resort" --city "Miami, FL" \
    --email "info@sunsetcoveresort.com" --phone "+1-305-555-0199" \
    --website "http://sunsetcoveresort.com" \
    --notes "No direct booking engine; redirects to Booking.com"

# List all leads (filter by status, or dump JSON for processing)
python scripts/lead_manager.py list
python scripts/lead_manager.py list --status emailed
python scripts/lead_manager.py list --json

# Advance a lead through the state machine
python scripts/lead_manager.py update lead-001 --status emailed --notes "Pitch sent"
python scripts/lead_manager.py update lead-001 --status replied   --notes "Wants demo"
python scripts/lead_manager.py update lead-001 --status closed_won --notes "Signed contract"

# See which leads need a follow-up right now + pipeline health
python scripts/lead_manager.py due
python scripts/lead_manager.py stats
python scripts/lead_manager.py export leads.csv    # CSV backup / spreadsheet
```

**Status state machine:** `identified → emailed → replied → proposal → closed_won`
(any open lead can be moved to `lost`). Open statuses (`identified/emailed/replied/proposal`)
are the ones the follow-up scheduler watches.

Sample pipeline state:

| ID | Hotel | Location | Status | Last action | Next step |
| :-- | :--- | :--- | :--- | :--- | :--- |
| lead-001 | Sunset Resort | Miami, FL | identified | 2026-08-26 | email pitch |
| lead-002 | Pine Hill Lodge | Aspen, CO | replied | 2026-08-26 | demo call Aug 29 |
| lead-003 | Harbor Inn | Boston, MA | proposal | 2026-08-25 | contract review |

---

## Automation Tooling (scripts)

This skill ships an automated lead-generation loop in `scripts/`. All run through
the system Python (`python <script>.py`), stdlib only.

### 1. Prospecting & audit — `prospect_finder.py`
Qualifies a hotel website against the three criteria (insecure HTTP, no direct
booking engine, OTA redirect) and emits a JSON verdict.

```bash
# Live audit of a candidate site (checks HTTPS, detects Booking/Expedia links)
python scripts/prospect_finder.py audit http://sunsetcoveresort.com

# Offline audit (paste an observed status) — no network needed
python scripts/prospect_finder.py audit http://sunsetcoveresort.com \
    --offline "No booking engine; redirects to booking.com"

# Optional: discover candidate hotels in an area (DuckDuckGo, best-effort, no key)
python scripts/prospect_finder.py find "boutique hotels Margate UK"
```

Pipe the verdict's `reason` straight into `lead_manager.py add --notes`.

### 2. Cost / ROI calculator — `roi_calculator.py`
Produces the concrete numbers used in the pitch (commission dollars lost, payback window):

```bash
python scripts/roi_calculator.py --rate 150 --rooms 20 --occupancy 0.7 --nights 3 \
    --commission 0.18 --capture 0.35 --build-cost 3500
```

### 3. Email sending — `outreach_sender.py`
Renders the personalized Template-1 pitch, with anti-spam safeguards.

```bash
# Preview (default — nothing sent)
python scripts/outreach_sender.py --dry-run
python scripts/outreach_sender.py --dry-run --id lead-001

# Actually send — ONLY after filling in data/config.json (SMTP creds, from_name)
python scripts/outreach_sender.py --commit --delay 2
```

**Anti-spam safeguards (enforced automatically):**
- Hard daily cap (`daily_limit`, default 30) and warm-up cap (`warmup_limit`, default 20) —
  start low for new domains.
- Skips any lead already emailed today; never bulk-sends.
- Injects an unsubscribe link into every email (legal requirement in many regions).
- Sends one-by-one with a delay; never fires without `data/config.json` SMTP settings.

### 4. Follow-up scheduler — `followup_scheduler.py`
Finds open leads whose `follow_up_date` has passed and (optionally) renders the
polite follow-up pitch before you send it.

```bash
python scripts/followup_scheduler.py          # who's due today/overdue
python scripts/followup_scheduler.py --due 5  # due within 5 days
python scripts/followup_scheduler.py --due 0 --render   # render follow-up email(s)
```

### 5. Client Cooperation, Objection Handling & Contract Closer — `deal_closer.py`
Analyzes client responses, generates cooperative counter-proposals that handle objections, and drafts formal web development agreements ready for signature.

```bash
# Handle client replies (auto-classifies intent or specify intent):
python scripts/deal_closer.py reply --id lead-001 --intent price
python scripts/deal_closer.py reply --id lead-001 --intent ota_objection
python scripts/deal_closer.py reply --id lead-001 --text "We already use Booking.com so why do we need this?"

# Generate formal Hotel Website & Direct Booking Agreement:
python scripts/deal_closer.py contract --id lead-001 --price 28000 --currency INR --out contract.md
```

### 6. Master Orchestrator CLI — `hotel_agent.py`
All-in-one command line interface and CRM web dashboard:

```bash
python hotel_agent.py find --city "Goa" --limit 10 --add
python hotel_agent.py list
python hotel_agent.py pitch --id lead-001
python hotel_agent.py reply --id lead-001 --intent price
python hotel_agent.py contract --id lead-001 --price 25000 --currency INR
python hotel_agent.py dashboard --port 8080
```

---

## Best Practices

1. **Personalization**: Never send generic spam. Mention specific details about their property (e.g., room count, amenities, city, or reviews).
2. **Follow-ups**: Send 1-2 polite follow-ups spaced 4-5 days apart if there is no response.
3. **Domain Security**: Ensure outreach emails pass SPF/DKIM validation so they land in the inbox.
