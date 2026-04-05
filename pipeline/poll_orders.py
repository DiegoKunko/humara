"""Humara — Poll for paid orders and run the translation pipeline.

Checks Supabase for orders with status='paid', downloads the client file,
and runs the pipeline automatically. Designed to be called by cron every 5 min.

Usage:
    python poll_orders.py

Environment variables (from .env):
    SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, ANTHROPIC_API_KEY, RESEND_API_KEY
"""

import json
import os
import sys
import time
from datetime import datetime

import requests

# Add pipeline dir to path
pipeline_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, pipeline_dir)

# Load .env
env_path = os.path.join(pipeline_dir, ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

from run_job import run, get_job_dir, update_order_status

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://uvhlverpjakhpwihhgef.supabase.co")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

# Default notification recipients
NOTIFY_EMAILS = "andrea.faraco@gmail.com,dpraderi@gmail.com,amalvasio@must.com.uy"
NOTIFY_NAME = "Andrea"

# Lock file to prevent concurrent runs
LOCK_FILE = os.path.join(pipeline_dir, ".poll_lock")


def get_headers():
    return {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
    }


def fetch_paid_orders():
    """Fetch all orders with status='paid'."""
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/orders?status=eq.paid&order=created_at.asc",
        headers=get_headers(),
        timeout=10,
    )
    if r.status_code == 200:
        return r.json()
    print(f"Error fetching orders: {r.status_code} {r.text}")
    return []


def download_client_file(order, job_dir):
    """Download the client's uploaded file from Supabase Storage to job_dir/input.pdf."""
    file_path = order.get("file_path")
    if not file_path:
        print(f"  Error: order {order['id']} has no file_path")
        return False

    os.makedirs(job_dir, exist_ok=True)
    input_path = os.path.join(job_dir, "input.pdf")

    # Download from Supabase Storage (documents bucket)
    r = requests.get(
        f"{SUPABASE_URL}/storage/v1/object/documents/{file_path}",
        headers={
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        },
        timeout=60,
    )

    if r.status_code == 200:
        with open(input_path, "wb") as f:
            f.write(r.content)
        size_mb = len(r.content) / (1024 * 1024)
        print(f"  Downloaded {file_path} ({size_mb:.1f} MB)")
        return True
    else:
        print(f"  Error downloading file: {r.status_code} {r.text}")
        return False


def map_doc_type(order_doc_type):
    """Map frontend doc_type values to pipeline doc_type values."""
    mapping = {
        "general": "general",
        "partida_nacimiento": "civil",
        "legal": "legal",
        "technical": "technical",
        "commercial": "commercial",
    }
    return mapping.get(order_doc_type, "general")


def process_order(order):
    """Process a single paid order through the pipeline."""
    order_id = order["id"]
    # Use order ID (first 8 chars) as job ID for the directory
    job_id = f"order-{order_id[:8]}"
    job_dir = get_job_dir(job_id)

    print(f"\n{'='*60}")
    print(f"Processing order {order_id[:8]}...")
    print(f"  File: {order.get('file_name', 'unknown')}")
    print(f"  Words: {order.get('word_count', 0)}")
    print(f"  Doc type: {order.get('doc_type', 'general')}")
    print(f"  Direction: {order.get('direction', 'en-es')}")

    # Download the file
    if not download_client_file(order, job_dir):
        update_order_status(order_id, "failed",
                            extra_fields={"error_message": "Could not download uploaded file"})
        return False

    # Map doc type
    doc_type = map_doc_type(order.get("doc_type", "general"))

    # Run the pipeline
    try:
        run(
            job_id=job_id,
            doc_type=doc_type,
            notify_email=NOTIFY_EMAILS,
            notify_name=NOTIFY_NAME,
            order_id=order_id,
        )
        print(f"  Order {order_id[:8]} completed successfully")
        return True
    except Exception as e:
        print(f"  Order {order_id[:8]} failed: {e}")
        # run() already updates the order status to 'failed'
        return False


def acquire_lock():
    """Simple file-based lock to prevent concurrent polling."""
    if os.path.exists(LOCK_FILE):
        # Check if lock is stale (older than 60 minutes)
        age = time.time() - os.path.getmtime(LOCK_FILE)
        if age < 3600:
            print(f"Another poll_orders is running (lock age: {age:.0f}s). Skipping.")
            return False
        print(f"Removing stale lock (age: {age:.0f}s)")
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    return True


def release_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)


def main():
    if not SUPABASE_SERVICE_KEY:
        print("Error: SUPABASE_SERVICE_ROLE_KEY not set")
        sys.exit(1)

    if not acquire_lock():
        return

    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Polling for paid orders...")
        orders = fetch_paid_orders()

        if not orders:
            print("No paid orders to process.")
            return

        print(f"Found {len(orders)} paid order(s) to process.")

        for order in orders:
            process_order(order)

        print(f"\nDone. Processed {len(orders)} order(s).")
    finally:
        release_lock()


if __name__ == "__main__":
    main()
