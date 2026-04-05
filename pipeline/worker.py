"""Humara Pipeline Worker — runs continuously, polling for paid orders.

Designed to run on Railway (or any cloud server) as a long-running process.
Replaces the local cron-based poll_orders.py approach.

Usage:
    python worker.py

Environment variables (required):
    SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, ANTHROPIC_API_KEY, RESEND_API_KEY
"""

import os
import sys
import time
import signal
from datetime import datetime

# Add pipeline dir to path
pipeline_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, pipeline_dir)

# Load .env if present (local dev only — Railway uses env vars directly)
env_path = os.path.join(pipeline_dir, ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

from poll_orders import fetch_paid_orders, process_order

POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "60"))  # seconds between polls
running = True


def shutdown(signum, frame):
    global running
    print(f"\n[{now()}] Shutting down gracefully...")
    running = False


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    print(f"[{now()}] Humara Pipeline Worker started")
    print(f"[{now()}] Polling every {POLL_INTERVAL}s")
    print(f"[{now()}] SUPABASE_URL: {os.environ.get('SUPABASE_URL', 'NOT SET')[:40]}...")
    print(f"[{now()}] ANTHROPIC_API_KEY: {'SET' if os.environ.get('ANTHROPIC_API_KEY') else 'NOT SET'}")
    print(f"[{now()}] RESEND_API_KEY: {'SET' if os.environ.get('RESEND_API_KEY') else 'NOT SET'}")
    sys.stdout.flush()

    while running:
        try:
            orders = fetch_paid_orders()
            if orders:
                print(f"[{now()}] Found {len(orders)} paid order(s)")
                sys.stdout.flush()
                for order in orders:
                    if not running:
                        break
                    process_order(order)
            else:
                print(f"[{now()}] No orders pending")

        except Exception as e:
            print(f"[{now()}] Error during poll: {e}")

        sys.stdout.flush()

        # Sleep in small increments so we can respond to SIGTERM quickly
        for _ in range(POLL_INTERVAL):
            if not running:
                break
            time.sleep(1)

    print(f"[{now()}] Worker stopped")


if __name__ == "__main__":
    main()
