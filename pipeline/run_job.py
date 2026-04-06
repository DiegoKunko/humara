"""Humara Translation Pipeline — Job Orchestrator (v2).

Usage:
    python run_job.py <job_id> [--doc-type legal|civil|technical|commercial|general]
    python run_job.py <job_id> --order-id <uuid> [--doc-type legal]

The job directory (pipeline/jobs/<job_id>/) must contain an input.pdf file.
When --order-id is provided, the pipeline updates the order status in Supabase.

Example:
    mkdir -p pipeline/jobs/job-001
    cp document.pdf pipeline/jobs/job-001/input.pdf
    python run_job.py job-001 --doc-type legal
"""

import json
import os
import sys
import time
import traceback
from datetime import datetime

import requests

# Add pipeline dir to path for imports
pipeline_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, pipeline_dir)

# Load .env if present
env_path = os.path.join(pipeline_dir, ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

from extract import extract_pdf
from extract_ocr import extract_pdf_ocr
from translate_v2 import translate_document
from review_v2 import review_document
from rebuild import rebuild_document
from upload import upload_job
from notify import notify_translator
from cost_tracker import CostTracker
from autocorrect import auto_correct_loop

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://uvhlverpjakhpwihhgef.supabase.co")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

# Config del loop de auto-corrección (override via env vars).
#
# Reviewer = Sonnet por default (calibrado abril 2026): Sonnet detecta los
# mismos errores reales que Opus pero sub-clasifica severidades (mayor→menor)
# y cuesta 5x menos y corre 2x más rápido. Budget estimado por job completo:
# ~$2-3 USD con Sonnet (vs $7-8 con Opus). Target subido a 0.92 para compensar
# el sesgo de Sonnet hacia scores más altos.
#
# Si algún job crítico necesita máxima severidad, setear HUMARA_REVIEW_MODEL=
# claude-opus-4-20250514 via env var.
AUTOCORRECT_TARGET_SCORE = float(os.environ.get("HUMARA_TARGET_SCORE", "0.92"))
AUTOCORRECT_MAX_ATTEMPTS = int(os.environ.get("HUMARA_MAX_ATTEMPTS", "3"))
AUTOCORRECT_COST_BUDGET = float(os.environ.get("HUMARA_COST_BUDGET_USD", "6.00"))
REVIEW_MODEL = os.environ.get("HUMARA_REVIEW_MODEL", "claude-sonnet-4-20250514")


def get_job_dir(job_id):
    """Get the absolute path to a job directory."""
    return os.path.join(os.path.dirname(__file__), "jobs", job_id)


def update_order_status(order_id, status, extra_fields=None):
    """Update an order's status in Supabase. No-op if order_id is None."""
    if not order_id or not SUPABASE_SERVICE_KEY:
        return
    payload = {"status": status}
    if extra_fields:
        payload.update(extra_fields)
    try:
        requests.patch(
            f"{SUPABASE_URL}/rest/v1/orders?id=eq.{order_id}",
            headers={
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            json=payload,
            timeout=10,
        )
    except Exception as e:
        print(f"  Warning: could not update order status: {e}")


def update_status(job_dir, status, step=None, progress=None):
    """Update the job status file."""
    status_path = os.path.join(job_dir, "status.json")

    data = {}
    if os.path.exists(status_path):
        with open(status_path, "r") as f:
            data = json.load(f)

    data.update({
        "status": status,
        "updated_at": datetime.now().isoformat(),
    })
    if step is not None:
        data["step"] = step
    if progress is not None:
        data["progress"] = progress
    if "started_at" not in data:
        data["started_at"] = data["updated_at"]

    with open(status_path, "w") as f:
        json.dump(data, f, indent=2)


def load_json(path):
    """Load a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run(job_id, doc_type="general", notify_email=None, notify_name="Traductor/a", order_id=None):
    """Run the full translation pipeline for a job.

    Args:
        order_id: If provided, updates the order status in Supabase at each step.
    """
    job_dir = get_job_dir(job_id)
    input_pdf = os.path.join(job_dir, "input.pdf")

    if not os.path.exists(job_dir):
        print(f"Error: Job directory not found: {job_dir}")
        sys.exit(1)

    if not os.path.exists(input_pdf):
        print(f"Error: input.pdf not found in {job_dir}")
        sys.exit(1)

    print(f"=== Humara Pipeline v2 — Job: {job_id} (doc_type={doc_type}) ===\n")
    start = time.time()
    update_order_status(order_id, "processing")

    # Cost tracker para todo el job
    cost_tracker = CostTracker(job_id, job_dir)

    # Estado del loop de auto-corrección (se llena después del review)
    loop_result = None
    warning_payload = None

    try:
        # Step 1: Extract (with automatic OCR fallback for scanned PDFs)
        extracted_path = os.path.join(job_dir, "extracted.json")
        if os.path.exists(extracted_path):
            print("[Step 1/4] Extract — using cached result")
            extracted = load_json(extracted_path)
        else:
            print("[Step 1/4] Extract — extracting PDF layout...")
            update_status(job_dir, "extracting", step=1)
            extracted = extract_pdf(input_pdf, job_dir)

            # Check if PDF is a scan (no text blocks found)
            text_block_count = sum(
                1 for p in extracted["pages"]
                for b in p["blocks"] if b["type"] == "text"
            )
            if text_block_count == 0:
                print("  ⚠ No text found — PDF is a scan. Switching to OCR...")
                extracted = extract_pdf_ocr(input_pdf, job_dir)

        print(f"  → {extracted['metadata']['pages']} pages extracted\n")

        # Step 2: Translate (v2 — Sonnet + glossary injection)
        translated_path = os.path.join(job_dir, "translated.json")
        if os.path.exists(translated_path):
            print("[Step 2/4] Translate v2 — using cached result")
            translated = load_json(translated_path)
        else:
            print("[Step 2/4] Translate v2 — translating with Claude Sonnet...")
            update_status(job_dir, "translating", step=2)
            update_order_status(order_id, "translating")
            translated = translate_document(
                extracted, job_dir, doc_type=doc_type, cost_tracker=cost_tracker
            )
        print()

        # Step 3: Review (v2 — Opus + 7-dimension review)
        reviewed_path = os.path.join(job_dir, "reviewed.json")
        if os.path.exists(reviewed_path):
            print("[Step 3/4] Review v2 — using cached result")
            reviewed_data = load_json(reviewed_path)
            print(f"  Skipping auto-correct loop (cached review)")
        else:
            print("[Step 3/4] Review v2 — reviewing with Claude Opus...")
            update_status(job_dir, "reviewing", step=3)
            update_order_status(order_id, "reviewing")
            reviewed_data = review_document(
                translated, job_dir, doc_type=doc_type,
                model=REVIEW_MODEL,
                cost_tracker=cost_tracker, attempt=1,
            )

            # Auto-correct loop: itera review hasta alcanzar target_score o agotar budget
            loop_result = auto_correct_loop(
                reviewed_data=reviewed_data,
                output_dir=job_dir,
                doc_type=doc_type,
                model=REVIEW_MODEL,
                cost_tracker=cost_tracker,
                target_score=AUTOCORRECT_TARGET_SCORE,
                max_attempts=AUTOCORRECT_MAX_ATTEMPTS,
                cost_budget_usd=AUTOCORRECT_COST_BUDGET,
            )
            reviewed_data = loop_result.final_reviewed
            warning_payload = loop_result.warning_payload
            update_status(job_dir, "reviewing", step=3, progress={
                "score": loop_result.final_report.get("score"),
                "attempts": loop_result.attempts_used,
                "reached_target": loop_result.reached_target,
                "stopped_by": loop_result.stopped_by,
            })
        print()

        # Step 4: Rebuild
        print("[Step 4/4] Rebuild — generating PDF...")
        update_status(job_dir, "rebuilding", step=4)
        pdf_path = rebuild_document(reviewed_data, job_dir)
        print()

        # Step 5: Upload to Supabase Storage
        print("[Step 5/5] Upload — pushing to Supabase Storage...")
        update_status(job_dir, "uploading", step=5)
        docx_path = os.path.join(job_dir, "traduccion.docx")
        urls = upload_job(job_id, job_dir, docx_path=docx_path if os.path.exists(docx_path) else None)
        print()

        # Step 6: Notify translator (if email provided)
        if notify_email:
            print("[Step 6/6] Notify — sending email to translator...")
            update_status(job_dir, "notifying", step=6)
            notify_translator(
                job_id, job_dir, notify_email, notify_name,
                warning_payload=warning_payload,
            )
            print()

        # Done — update order with output paths + cost/quality metrics
        elapsed = time.time() - start
        total_steps = 6 if notify_email else 5
        update_status(job_dir, "done", step=total_steps, progress=f"completed in {elapsed:.0f}s")

        # Sincronizar costos a Supabase (tabla job_llm_calls)
        cost_tracker.sync_to_supabase()

        # Cargar el review_report final para los metadata del order
        final_report_path = os.path.join(job_dir, "review_report.json")
        final_report = load_json(final_report_path) if os.path.exists(final_report_path) else {}

        inp_tokens, out_tokens = cost_tracker.total_tokens()
        output_fields = {
            "output_path": f"{job_id}/traduccion.docx",
            "job_id": job_id,
            "ai_cost_usd": round(cost_tracker.total_usd(), 4),
            "ai_tokens_input": inp_tokens,
            "ai_tokens_output": out_tokens,
            "review_score": final_report.get("score"),
            "review_attempts": loop_result.attempts_used if loop_result else 1,
            "review_reached_target": loop_result.reached_target if loop_result else None,
            "unresolved_issues": warning_payload,
        }
        update_order_status(order_id, "ready", extra_fields=output_fields)

        print(f"=== Done in {elapsed:.0f}s ===")
        print(f"AI cost: ${cost_tracker.total_usd():.4f}")
        if loop_result:
            print(f"Final score: {loop_result.final_report.get('score', 0):.3f} "
                  f"({'✓ target reached' if loop_result.reached_target else '✗ below target'})")
        if pdf_path:
            print(f"Output PDF: {pdf_path}")
        if urls:
            print(f"Download URLs saved: {os.path.join(job_dir, 'download_urls.json')}")

    except Exception as e:
        elapsed = time.time() - start
        error_msg = f"{type(e).__name__}: {e}"
        print(f"\n=== FAILED after {elapsed:.0f}s: {error_msg} ===")
        traceback.print_exc()
        update_status(job_dir, "failed", progress=error_msg)
        update_order_status(order_id, "failed", extra_fields={"error_message": error_msg[:500]})
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Humara Translation Pipeline v2")
    parser.add_argument("job_id", help="Job ID (directory name under pipeline/jobs/)")
    parser.add_argument("--doc-type", default="general",
                        choices=["legal", "civil", "technical", "auto", "commercial", "general"],
                        help="Document type for glossary selection (default: general)")
    parser.add_argument("--notify", metavar="EMAIL",
                        help="Send notification email to translator when done")
    parser.add_argument("--notify-name", default="Traductor/a",
                        help="Translator name for the email greeting")
    parser.add_argument("--order-id", metavar="UUID",
                        help="Supabase order ID to update status in real-time")
    args = parser.parse_args()
    run(args.job_id, doc_type=args.doc_type,
        notify_email=args.notify, notify_name=args.notify_name,
        order_id=args.order_id)
