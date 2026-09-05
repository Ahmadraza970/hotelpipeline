#!/usr/bin/env python3
"""
roi_calculator.py - OTA commission-loss & ROI calculator for the hotel pitch.

Arithmetic only, stdlib. Produces the concrete numbers that make the cold
email / demo compelling:

  * avg nightly rate
  * avg nights per stay
  * occupied room-nights per month (rooms  x  occupancy  x  nights  x 30)
  * OTA commission loss per reservation and per month / per year
  * projected direct-booking capture (what % of OTA volume shifts to direct)
  * build cost -> payback / ROI window

Usage:
  python roi_calculator.py --rate 150 --rooms 20 --occupancy 0.7 --nights 3 \
       --commission 0.18 --capture 0.35 --build-cost 3500
"""
import argparse


def money(v):
    return "$%s" % format(round(v), ",")


def main():
    p = argparse.ArgumentParser(description="Hotel OTA commission-loss / ROI calculator")
    p.add_argument("--rate", type=float, required=True, help="Avg nightly rate, e.g. 150")
    p.add_argument("--rooms", type=int, required=True, help="Number of rooms")
    p.add_argument("--occupancy", type=float, default=0.7, help="Occupancy rate 0-1")
    p.add_argument("--nights", type=float, default=3.0, help="Avg nights per stay")
    p.add_argument("--commission", type=float, default=0.18, help="OTA commission 0-1")
    p.add_argument("--capture", type=float, default=0.35, help="Share of OTA volume shifted to direct 0-1")
    p.add_argument("--build-cost", type=float, default=3500, help="One-time website build cost")
    args = p.parse_args()

    room_nights_month = args.rooms * args.occupancy * 30.0
    reservations_month = room_nights_month / max(args.nights, 0.1)
    revenue_month = room_nights_month * args.rate
    commission_loss_month = revenue_month * args.commission
    commission_loss_year = commission_loss_month * 12

    direct_gain_month = commission_loss_month * args.capture
    direct_gain_year = direct_gain_month * 12

    payback_months = args.build_cost / max(direct_gain_month, 0.01)

    print("=== OTA Commission Loss ===")
    print("  Occupied room-nights / month : %d" % round(room_nights_month))
    print("  Reservations / month         : %d" % round(reservations_month))
    print("  OTA revenue / month          : %s" % money(revenue_month))
    print("  Commission lost / month      : %s  (%d%%)" % (money(commission_loss_month), round(args.commission * 100)))
    print("  Commission lost / year       : %s" % money(commission_loss_year))
    print()
    print("=== Direct-Booking Value Prop ===")
    print("  Capture rate                  : %d%%" % round(args.capture * 100))
    print("  Wasted commission captured    : %s / month" % money(direct_gain_month))
    print("  Wasted commission captured    : %s / year" % money(direct_gain_year))
    print()
    print("=== ROI on Build Cost (%s) ===" % money(args.build_cost))
    print("  Payback period                : %.1f months" % payback_months)
    if payback_months <= 12:
        print("  Verdict                       : Payback within the first year — strong pitch.")
    else:
        print("  Verdict                       : Payback beyond a year; lean on recurring-convenience value.")


if __name__ == "__main__":
    main()