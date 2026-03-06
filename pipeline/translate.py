"""Step 2: Translate extracted text blocks using Claude API."""

import json
import os
import time

import anthropic


def load_prompt(prompt_name):
    """Load a system prompt from the prompts directory."""
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", prompt_name)
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def chunk_pages(pages, max_blocks=50):
    """Split pages into chunks of manageable size for the API.

    Groups consecutive pages until we hit max_blocks text blocks per chunk.
    """
    chunks = []
    current_chunk = []
    current_block_count = 0

    for page in pages:
        text_blocks = [b for b in page["blocks"] if b["type"] == "text"]
        if current_block_count + len(text_blocks) > max_blocks and current_chunk:
            chunks.append(current_chunk)
            current_chunk = []
            current_block_count = 0
        current_chunk.append(page)
        current_block_count += len(text_blocks)

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def translate_chunk(client, system_prompt, chunk, source_lang="en", target_lang="es"):
    """Translate a chunk of pages via Claude API.

    Args:
        client: Anthropic client
        system_prompt: System prompt for the translator
        chunk: List of page dicts with blocks
        source_lang: Source language code
        target_lang: Target language code

    Returns:
        List of translated page dicts
    """
    # Build the text-only payload for translation
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

    # Parse response
    response_text = response.content[0].text
    # Strip markdown code fences if present
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

    translated = json.loads(response_text)

    # Merge translations back into the original chunk structure
    translated_lookup = {}
    for page_data in translated:
        page_num = page_data["page"]
        for text_item in page_data["texts"]:
            translated_lookup[(page_num, text_item["index"])] = text_item["text"]

    result = []
    for page in chunk:
        new_page = {**page, "blocks": []}
        for i, block in enumerate(page["blocks"]):
            if block["type"] == "text":
                key = (page["page"], i)
                new_block = {**block, "text": translated_lookup.get(key, block["text"])}
                new_page["blocks"].append(new_block)
            else:
                new_page["blocks"].append(block)
        result.append(new_page)

    return result


def translate_document(extracted_data, output_dir):
    """Translate all pages in the extracted data.

    Args:
        extracted_data: Dict with metadata and pages from extract step
        output_dir: Job directory to save translated.json

    Returns:
        Dict with translated pages
    """
    client = anthropic.Anthropic()
    system_prompt = load_prompt("translator.txt")

    pages = extracted_data["pages"]
    chunks = chunk_pages(pages)
    translated_pages = []

    print(f"  Translating {len(pages)} pages in {len(chunks)} chunks...")

    for i, chunk in enumerate(chunks):
        page_range = f"{chunk[0]['page']}-{chunk[-1]['page']}"
        print(f"  Chunk {i + 1}/{len(chunks)} (pages {page_range})...")

        try:
            translated = translate_chunk(client, system_prompt, chunk)
            translated_pages.extend(translated)
        except Exception as e:
            print(f"  Error on chunk {i + 1}: {e}")
            print(f"  Retrying in 5s...")
            time.sleep(5)
            try:
                translated = translate_chunk(client, system_prompt, chunk)
                translated_pages.extend(translated)
            except Exception as e2:
                print(f"  Failed again: {e2}. Keeping original text for this chunk.")
                translated_pages.extend(chunk)

        # Rate limiting — pause between chunks
        if i < len(chunks) - 1:
            time.sleep(1)

    result = {
        "metadata": {**extracted_data["metadata"], "target_lang": "es"},
        "pages": translated_pages,
    }

    output_path = os.path.join(output_dir, "translated.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"  Translated {len(translated_pages)} pages → {output_path}")
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python translate.py <extracted.json> <output_dir>")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)
    translate_document(data, sys.argv[2])
