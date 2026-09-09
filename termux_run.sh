#!/bin/bash
# Termux runner for Hermes Hotel Pipeline
# Usage: bash termux_run.sh [discovery|send|full|status]
# Auto-detects working directory

set -e

# Detect working directory (Termux clone path or local)
if [ -d "$HOME/hermes" ]; then
    HERMES_DIR="$HOME/hermes"
elif [ -d "/data/data/com.termux/files/home/hermes" ]; then
    HERMES_DIR="/data/data/com.termux/files/home/hermes"
else
    HERMES_DIR="$(pwd)"
fi

export HERMES_DIR="$HERMES_DIR"
echo "📁 Working dir: $HERMES_DIR"

MODE="${1:-full}"

case "$MODE" in
    discovery)
        echo "🧭 Running USA discovery..."
        cd "$HERMES_DIR"
        python3 usa_hotel_agent.py --all --limit 10
        python3 us_serper_live.py
        ;;
    send)
        echo "📤 Running outreach (dry-run preview)..."
        cd "$HERMES_DIR"
        python3 .agents/skills/hotel-website-outreach/scripts/outreach_sender.py --dry-run
        ;;
    send-commit)
        echo "📤 Committing outreach sends..."
        cd "$HERMES_DIR"
        python3 .agents/skills/hotel-website-outreach/scripts/outreach_sender.py --commit --delay 2
        ;;
    status)
        echo "📊 Pipeline status..."
        cd "$HERMES_DIR"
        python3 telegram_notifier.py status
        ;;
    full)
        echo "🚀 Full pipeline run..."
        cd "$HERMES_DIR"
        python3 telegram_notifier.py status
        echo "---"
        python3 usa_hotel_agent.py --all --limit 10
        echo "---"
        python3 us_serper_live.py
        echo "---"
        python3 .agents/skills/hotel-website-outreach/scripts/outreach_sender.py --dry-run
        echo "---"
        python3 telegram_notifier.py status
        ;;
    *)
        echo "Usage: bash termux_run.sh [discovery|send|send-commit|status|full]"
        exit 1
        ;;
esac

echo ""
echo "✅ Done — $(date)"