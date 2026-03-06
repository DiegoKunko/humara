"""Step 3 (v2): Professional review with quality report and structured feedback."""

import json
import os
import sys
import time

import anthropic

from translate_v2 import load_glossaries, load_prompt, chunk_pages

PROMPT_DIR = os.path.join(os.path.dirname(__file__), "prompts")


def build_review_prompt(doc_type):
    """Build the full review system prompt with glossary injected."""
    base_prompt = load_prompt("reviewer_v2.txt")
    glossary_text = load_glossaries(doc_type)
    return base_prompt.replace("{glossary_placeholder}", glossary_text)


def review_chunk(client, system_prompt, chunk, model="claude-opus-4-20250514"):
    """Review a chunk of translated pages via Claude API.

    Returns:
        tuple: (reviewed_pages, issues_list, segments_modified)
    """
    text_payload = []
    for page in chunk:
        page_texts = []
        for i, block in enumerate(page["blocks"]):
            if block["type"] == "text":
                page_texts.append({"index": i, "text": block["text"]})
        text_payload.append({
            "page": page["page"],
            "texts": page_texts,
        })

    user_message = json.dumps(text_payload, ensure_ascii=False)

    response = client.messages.create(
        model=model,
        max_tokens=16384,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    response_text = response.content[0].text
    # Strip markdown code fences if present
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

    review_data = json.loads(response_text)

    # Extract reviewed pages
    reviewed_pages_data = review_data.get("reviewed_pages", [])
    report = review_data.get("review_report", {})

    # Merge reviewed text back into the original chunk structure
    reviewed_lookup = {}
    for page_data in reviewed_pages_data:
        page_num = page_data["page"]
        for text_item in page_data["texts"]:
            reviewed_lookup[(page_num, text_item["index"])] = text_item["text"]

    result = []
    changes = 0
    for page in chunk:
        new_page = {**page, "blocks": []}
        for i, block in enumerate(page["blocks"]):
            if block["type"] == "text":
                key = (page["page"], i)
                new_text = reviewed_lookup.get(key, block["text"])
                if new_text != block["text"]:
                    changes += 1
                new_block = {**block, "text": new_text}
                new_page["blocks"].append(new_block)
            else:
                new_page["blocks"].append(block)
        result.append(new_page)

    issues = report.get("issues", [])
    score = report.get("score", 0.0)
    ready = report.get("ready_for_certification", False)
    summary = report.get("summary", "")

    return result, issues, changes, score, ready, summary


def review_document(translated_data, output_dir, doc_type="general",
                    model="claude-opus-4-20250514"):
    """Review all pages in the translated data.

    Args:
        translated_data: Dict with translated pages from translate step
        output_dir: Job directory to save reviewed.json and review_report.json
        doc_type: Document type for glossary selection
        model: Claude model to use (Opus recommended for review)

    Returns:
        Dict with reviewed pages
    """
    client = anthropic.Anthropic()
    system_prompt = build_review_prompt(doc_type)

    prompt_tokens_approx = len(system_prompt.split())
    print(f"  Review prompt: ~{prompt_tokens_approx} words (doc_type={doc_type})")

    pages = translated_data["pages"]
    # Use smaller chunks for review to give the model more room for analysis
    chunks = chunk_pages(pages, max_blocks=30)
    reviewed_pages = []
    all_issues = []
    total_changes = 0
    total_segments = 0
    chunk_scores = []

    print(f"  Reviewing {len(pages)} pages in {len(chunks)} chunks (model={model})...")

    for i, chunk in enumerate(chunks):
        page_range = f"{chunk[0]['page']}-{chunk[-1]['page']}"
        seg_count = sum(
            1 for p in chunk for b in p["blocks"] if b["type"] == "text"
        )
        total_segments += seg_count
        print(f"  Chunk {i + 1}/{len(chunks)} (pages {page_range}, {seg_count} segments)...")

        try:
            reviewed, issues, changes, score, ready, summary = review_chunk(
                client, system_prompt, chunk, model=model
            )
            reviewed_pages.extend(reviewed)
            all_issues.extend(issues)
            total_changes += changes
            chunk_scores.append((seg_count, score))

            status = "✓ READY" if ready else f"✗ {len(issues)} issues"
            print(f"    Score: {score:.2f} | Changes: {changes} | {status}")

        except Exception as e:
            print(f"  Error on chunk {i + 1}: {e}")
            print(f"  Retrying in 5s...")
            time.sleep(5)
            try:
                reviewed, issues, changes, score, ready, summary = review_chunk(
                    client, system_prompt, chunk, model=model
                )
                reviewed_pages.extend(reviewed)
                all_issues.extend(issues)
                total_changes += changes
                chunk_scores.append((seg_count, score))
            except Exception as e2:
                print(f"  Failed again: {e2}. Keeping translated text for this chunk.")
                reviewed_pages.extend(chunk)
                chunk_scores.append((seg_count, 0.0))

        # Rate limiting
        if i < len(chunks) - 1:
            time.sleep(1)

    # Calculate weighted average score
    if chunk_scores:
        total_weight = sum(w for w, _ in chunk_scores)
        avg_score = sum(w * s for w, s in chunk_scores) / total_weight if total_weight else 0.0
    else:
        avg_score = 0.0

    # Count issues by severity
    critical = sum(1 for iss in all_issues if iss.get("severity") == "critico")
    major = sum(1 for iss in all_issues if iss.get("severity") == "mayor")
    minor = sum(1 for iss in all_issues if iss.get("severity") == "menor")

    overall_ready = avg_score >= 0.95 and critical == 0 and major == 0

    # Save reviewed text
    result = {
        "metadata": {
            **translated_data.get("metadata", {}),
            "reviewer_version": "v2",
            "review_model": model,
            "review_score": round(avg_score, 3),
            "ready_for_certification": overall_ready,
        },
        "pages": reviewed_pages,
    }

    reviewed_path = os.path.join(output_dir, "reviewed.json")
    with open(reviewed_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Save review report
    report = {
        "score": round(avg_score, 3),
        "ready_for_certification": overall_ready,
        "total_segments": total_segments,
        "segments_modified": total_changes,
        "issues_summary": {
            "total": len(all_issues),
            "critical": critical,
            "major": major,
            "minor": minor,
        },
        "issues": all_issues,
    }

    report_path = os.path.join(output_dir, "review_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Print summary
    print(f"\n  ═══ REVIEW SUMMARY ═══")
    print(f"  Score: {avg_score:.3f} / 1.000")
    print(f"  Ready for certification: {'YES ✓' if overall_ready else 'NO ✗'}")
    print(f"  Segments: {total_segments} total, {total_changes} modified")
    print(f"  Issues: {critical} critical, {major} major, {minor} minor")
    print(f"  Output: {reviewed_path}")
    print(f"  Report: {report_path}")

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Review translated text (v2)")
    parser.add_argument("input", help="Path to translated.json")
    parser.add_argument("output_dir", help="Job output directory")
    parser.add_argument("--doc-type", default="general",
                        choices=["legal", "civil", "technical", "auto", "commercial", "general"],
                        help="Document type for glossary selection")
    parser.add_argument("--model", default="claude-opus-4-20250514",
                        help="Claude model for review (Opus recommended)")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    review_document(data, args.output_dir, doc_type=args.doc_type, model=args.model)
