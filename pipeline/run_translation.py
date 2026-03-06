"""Pipeline orchestrator: Extract → Translate (v2) → Review (v2).

Usage:
    python run_translation.py input.pdf --doc-type legal --output jobs/my-job/
    python run_translation.py input.docx --doc-type commercial --direction en-es
    python run_translation.py jobs/test-001/extracted.json --doc-type technical --pages 29-31
"""

import argparse
import json
import os
import sys
import time

from extract_documents import extract_document
from translate_v2 import translate_document
from review_v2 import review_document


def filter_pages(data, page_spec):
    """Filter pages by page spec (e.g., '29-43,70-72,134-136')."""
    if not page_spec:
        return data

    # Parse page spec
    requested = set()
    for part in page_spec.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            requested.update(range(int(start), int(end) + 1))
        else:
            requested.add(int(part))

    filtered_pages = [p for p in data["pages"] if p["page"] in requested]

    if not filtered_pages:
        print(f"  Warning: no pages matched spec '{page_spec}'")
        print(f"  Available pages: {[p['page'] for p in data['pages'][:10]]}...")

    return {
        "metadata": {**data.get("metadata", {}), "page_filter": page_spec},
        "pages": filtered_pages,
    }


def run_pipeline(input_path, output_dir, doc_type="general", page_spec=None,
                 translate_model="claude-sonnet-4-20250514",
                 review_model="claude-opus-4-20250514",
                 skip_review=False):
    """Run the full translation pipeline.

    Args:
        input_path: Path to input document (PDF, DOCX, TXT, JSON)
        output_dir: Directory for all outputs
        doc_type: Document type for glossary selection
        page_spec: Optional page filter (e.g., "29-43,70-72")
        translate_model: Model for translation step
        review_model: Model for review step
        skip_review: If True, skip the review step
    """
    os.makedirs(output_dir, exist_ok=True)
    start_time = time.time()

    print("═══════════════════════════════════════════")
    print("  PROFESSIONAL TRANSLATION PIPELINE v2")
    print("═══════════════════════════════════════════")
    print(f"  Input: {input_path}")
    print(f"  Output: {output_dir}")
    print(f"  Doc type: {doc_type}")
    print(f"  Translate model: {translate_model}")
    print(f"  Review model: {review_model}")
    if page_spec:
        print(f"  Page filter: {page_spec}")
    print("═══════════════════════════════════════════\n")

    # Step 1: Extract
    print("▸ STEP 1: EXTRACT")
    extracted = extract_document(input_path, output_dir)

    # Apply page filter if specified
    if page_spec:
        extracted = filter_pages(extracted, page_spec)
        print(f"  Filtered to {len(extracted['pages'])} pages\n")
    else:
        print()

    if not extracted["pages"]:
        print("  ERROR: No pages to process. Aborting.")
        return None

    # Step 2: Translate
    print("▸ STEP 2: TRANSLATE")
    translated = translate_document(
        extracted, output_dir,
        doc_type=doc_type,
        model=translate_model,
    )
    print()

    # Step 3: Review
    if skip_review:
        print("▸ STEP 3: REVIEW (skipped)")
        reviewed = translated
    else:
        print("▸ STEP 3: REVIEW")
        reviewed = review_document(
            translated, output_dir,
            doc_type=doc_type,
            model=review_model,
        )
    print()

    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)

    print("═══════════════════════════════════════════")
    print("  PIPELINE COMPLETE")
    print(f"  Time: {minutes}m {seconds}s")
    print(f"  Pages processed: {len(reviewed['pages'])}")

    if not skip_review:
        score = reviewed.get("metadata", {}).get("review_score", "N/A")
        ready = reviewed.get("metadata", {}).get("ready_for_certification", False)
        print(f"  Quality score: {score}")
        print(f"  Ready for certification: {'YES ✓' if ready else 'NO ✗'}")

    print(f"  Output dir: {output_dir}")
    print("═══════════════════════════════════════════")

    return reviewed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Professional Translation Pipeline v2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Translate a legal PDF (English→Spanish, auto-detected)
  python run_translation.py contract.pdf --doc-type legal --output jobs/contract/

  # Translate specific pages from existing extracted JSON
  python run_translation.py jobs/test-001/extracted.json --doc-type technical --pages 29-43

  # Translate a Word document, commercial type
  python run_translation.py report.docx --doc-type commercial --output jobs/report/

  # Quick translate without review
  python run_translation.py input.txt --output jobs/quick/ --skip-review
        """
    )
    parser.add_argument("input", help="Input file (.pdf, .docx, .txt, .md, .json)")
    parser.add_argument("--output", "-o", default=None,
                        help="Output directory (default: auto-generated from input name)")
    parser.add_argument("--doc-type", "-t", default="general",
                        choices=["legal", "civil", "technical", "auto", "commercial", "general"],
                        help="Document type for glossary selection (default: general)")
    parser.add_argument("--pages", "-p", default=None,
                        help="Page filter, e.g. '29-43,70-72,134-136'")
    parser.add_argument("--translate-model", default="claude-sonnet-4-20250514",
                        help="Model for translation (default: claude-sonnet-4-20250514)")
    parser.add_argument("--review-model", default="claude-opus-4-20250514",
                        help="Model for review (default: claude-opus-4-20250514)")
    parser.add_argument("--skip-review", action="store_true",
                        help="Skip the review step (faster, less quality assurance)")

    args = parser.parse_args()

    # Auto-generate output dir if not specified
    if args.output is None:
        base = os.path.splitext(os.path.basename(args.input))[0]
        args.output = os.path.join("jobs", base)

    run_pipeline(
        input_path=args.input,
        output_dir=args.output,
        doc_type=args.doc_type,
        page_spec=args.pages,
        translate_model=args.translate_model,
        review_model=args.review_model,
        skip_review=args.skip_review,
    )
