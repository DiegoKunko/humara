"""Step 3: Proofread translated text using Claude API."""

import json
import os
import time

import anthropic

from translate import load_prompt, chunk_pages


def proofread_chunk(client, system_prompt, chunk):
    """Proofread a chunk of translated pages via Claude API."""
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
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    response_text = response.content[0].text
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

    proofread = json.loads(response_text)

    # Merge corrections back
    proofread_lookup = {}
    for page_data in proofread:
        page_num = page_data["page"]
        for text_item in page_data["texts"]:
            proofread_lookup[(page_num, text_item["index"])] = text_item["text"]

    result = []
    changes = 0
    for page in chunk:
        new_page = {**page, "blocks": []}
        for i, block in enumerate(page["blocks"]):
            if block["type"] == "text":
                key = (page["page"], i)
                new_text = proofread_lookup.get(key, block["text"])
                if new_text != block["text"]:
                    changes += 1
                new_block = {**block, "text": new_text}
                new_page["blocks"].append(new_block)
            else:
                new_page["blocks"].append(block)
        result.append(new_page)

    return result, changes


def proofread_document(translated_data, output_dir):
    """Proofread all pages in the translated data.

    Args:
        translated_data: Dict with translated pages from translate step
        output_dir: Job directory to save proofread.json

    Returns:
        Dict with proofread pages
    """
    client = anthropic.Anthropic()
    system_prompt = load_prompt("proofreader.txt")

    pages = translated_data["pages"]
    chunks = chunk_pages(pages)
    proofread_pages = []
    total_changes = 0

    print(f"  Proofreading {len(pages)} pages in {len(chunks)} chunks...")

    for i, chunk in enumerate(chunks):
        page_range = f"{chunk[0]['page']}-{chunk[-1]['page']}"
        print(f"  Chunk {i + 1}/{len(chunks)} (pages {page_range})...")

        try:
            proofread, changes = proofread_chunk(client, system_prompt, chunk)
            proofread_pages.extend(proofread)
            total_changes += changes
        except Exception as e:
            print(f"  Error on chunk {i + 1}: {e}")
            print(f"  Retrying in 5s...")
            time.sleep(5)
            try:
                proofread, changes = proofread_chunk(client, system_prompt, chunk)
                proofread_pages.extend(proofread)
                total_changes += changes
            except Exception as e2:
                print(f"  Failed again: {e2}. Keeping translated text for this chunk.")
                proofread_pages.extend(chunk)

        if i < len(chunks) - 1:
            time.sleep(1)

    result = {
        "metadata": {**translated_data["metadata"], "proofread_changes": total_changes},
        "pages": proofread_pages,
    }

    output_path = os.path.join(output_dir, "proofread.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"  Proofread {len(proofread_pages)} pages ({total_changes} corrections) → {output_path}")
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python proofread.py <translated.json> <output_dir>")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)
    proofread_document(data, sys.argv[2])
