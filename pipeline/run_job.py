"""Humara Translation Pipeline — Job Orchestrator.

Usage:
    python run_job.py <job_id>

The job directory (pipeline/jobs/<job_id>/) must contain an input.pdf file.

Example:
    mkdir -p pipeline/jobs/job-001
    cp document.pdf pipeline/jobs/job-001/input.pdf
    python run_job.py job-001
"""

import json
import os
import sys
import time
from datetime import datetime

# Add pipeline dir to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from extract import extract_pdf
from translate import translate_document
from proofread import proofread_document
from rebuild import rebuild_document


def get_job_dir(job_id):
    """Get the absolute path to a job directory."""
    return os.path.join(os.path.dirname(__file__), "jobs", job_id)


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


def run(job_id):
    """Run the full translation pipeline for a job."""
    job_dir = get_job_dir(job_id)
    input_pdf = os.path.join(job_dir, "input.pdf")

    if not os.path.exists(job_dir):
        print(f"Error: Job directory not found: {job_dir}")
        sys.exit(1)

    if not os.path.exists(input_pdf):
        print(f"Error: input.pdf not found in {job_dir}")
        sys.exit(1)

    print(f"=== Humara Pipeline — Job: {job_id} ===\n")
    start = time.time()

    # Step 1: Extract
    extracted_path = os.path.join(job_dir, "extracted.json")
    if os.path.exists(extracted_path):
        print("[Step 1/4] Extract — using cached result")
        extracted = load_json(extracted_path)
    else:
        print("[Step 1/4] Extract — extracting PDF layout...")
        update_status(job_dir, "extracting", step=1)
        extracted = extract_pdf(input_pdf, job_dir)
    print(f"  → {extracted['metadata']['pages']} pages extracted\n")

    # Step 2: Translate
    translated_path = os.path.join(job_dir, "translated.json")
    if os.path.exists(translated_path):
        print("[Step 2/4] Translate — using cached result")
        translated = load_json(translated_path)
    else:
        print("[Step 2/4] Translate — translating with Claude...")
        update_status(job_dir, "translating", step=2)
        translated = translate_document(extracted, job_dir)
    print()

    # Step 3: Proofread
    proofread_path = os.path.join(job_dir, "proofread.json")
    if os.path.exists(proofread_path):
        print("[Step 3/4] Proofread — using cached result")
        proofread_data = load_json(proofread_path)
    else:
        print("[Step 3/4] Proofread — reviewing with Claude...")
        update_status(job_dir, "proofreading", step=3)
        proofread_data = proofread_document(translated, job_dir)
    print()

    # Step 4: Rebuild
    print("[Step 4/4] Rebuild — generating PDF...")
    update_status(job_dir, "rebuilding", step=4)
    pdf_path = rebuild_document(proofread_data, job_dir)
    print()

    # Done
    elapsed = time.time() - start
    update_status(job_dir, "done", step=4, progress=f"completed in {elapsed:.0f}s")

    print(f"=== Done in {elapsed:.0f}s ===")
    if pdf_path:
        print(f"Output: {pdf_path}")
    else:
        print(f"HTML output: {os.path.join(job_dir, 'output.html')}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    run(sys.argv[1])
