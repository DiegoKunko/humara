"""Step 2 (v2): Professional translation with glossary injection and bidirectional support."""

import json
import os
import sys
import time

import anthropic

GLOSSARY_DIR = os.path.join(os.path.dirname(__file__), "glossaries")
PROMPT_DIR = os.path.join(os.path.dirname(__file__), "prompts")

# Map doc_type to which glossary files to load
DOC_TYPE_GLOSSARIES = {
    "legal": ["legal_en_es.json", "false_friends.json"],
    "civil": ["legal_en_es.json", "false_friends.json"],
    "technical": ["technical_en_es.json", "false_friends.json"],
    "auto": ["technical_en_es.json", "false_friends.json"],
    "commercial": ["commercial_en_es.json", "false_friends.json"],
    "general": ["false_friends.json"],
}


def load_prompt(prompt_name):
    """Load a system prompt from the prompts directory."""
    path = os.path.join(PROMPT_DIR, prompt_name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def load_glossaries(doc_type):
    """Load and merge glossary files for the given document type.

    Returns a formatted string suitable for injection into the system prompt.
    """
    files = DOC_TYPE_GLOSSARIES.get(doc_type, DOC_TYPE_GLOSSARIES["general"])
    all_terms = {}

    for filename in files:
        path = os.path.join(GLOSSARY_DIR, filename)
        if not os.path.exists(path):
            print(f"  Warning: glossary {filename} not found, skipping")
            continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "terms" in data:
            for category, terms in data["terms"].items():
                section_name = category.replace("_", " ").title()
                if section_name not in all_terms:
                    all_terms[section_name] = {}
                all_terms[section_name].update(terms)

        if "false_friends" in data:
            ff_lines = []
            for ff in data["false_friends"]:
                en = ff["en"]
                correct = ff.get("correct_es", "")
                false = ff.get("false_es", "")
                ff_lines.append(f"- {en} → {correct} (NO: {false})")
            all_terms["Falsos Amigos (lista completa)"] = "\n".join(ff_lines)

    # Format as readable text for the prompt
    parts = []
    for section, content in all_terms.items():
        parts.append(f"\n### {section}")
        if isinstance(content, dict):
            for en_term, es_term in content.items():
                parts.append(f"- {en_term} → {es_term}")
        else:
            parts.append(content)

    return "\n".join(parts)


def build_system_prompt(doc_type):
    """Build the full system prompt with glossary injected."""
    base_prompt = load_prompt("translator_v2.txt")
    glossary_text = load_glossaries(doc_type)
    return base_prompt.replace("{glossary_placeholder}", glossary_text)


def chunk_pages(pages, max_blocks=50):
    """Split pages into chunks of manageable size for the API."""
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


def translate_chunk(client, system_prompt, chunk, model="claude-sonnet-4-20250514"):
    """Translate a chunk of pages via Claude API."""
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
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

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


def translate_document(extracted_data, output_dir, doc_type="general",
                       model="claude-sonnet-4-20250514"):
    """Translate all pages in the extracted data.

    Args:
        extracted_data: Dict with metadata and pages from extract step
        output_dir: Job directory to save translated.json
        doc_type: Document type for glossary selection
        model: Claude model to use

    Returns:
        Dict with translated pages
    """
    client = anthropic.Anthropic()
    system_prompt = build_system_prompt(doc_type)

    # Log prompt size for debugging
    prompt_tokens_approx = len(system_prompt.split())
    print(f"  System prompt: ~{prompt_tokens_approx} words (doc_type={doc_type})")

    pages = extracted_data["pages"]
    chunks = chunk_pages(pages)
    translated_pages = []

    print(f"  Translating {len(pages)} pages in {len(chunks)} chunks...")

    for i, chunk in enumerate(chunks):
        page_range = f"{chunk[0]['page']}-{chunk[-1]['page']}"
        print(f"  Chunk {i + 1}/{len(chunks)} (pages {page_range})...")

        try:
            translated = translate_chunk(client, system_prompt, chunk, model=model)
            translated_pages.extend(translated)
        except Exception as e:
            print(f"  Error on chunk {i + 1}: {e}")
            print(f"  Retrying in 5s...")
            time.sleep(5)
            try:
                translated = translate_chunk(client, system_prompt, chunk, model=model)
                translated_pages.extend(translated)
            except Exception as e2:
                print(f"  Failed again: {e2}. Keeping original text for this chunk.")
                translated_pages.extend(chunk)

        # Rate limiting
        if i < len(chunks) - 1:
            time.sleep(1)

    result = {
        "metadata": {
            **extracted_data.get("metadata", {}),
            "doc_type": doc_type,
            "model": model,
            "translator_version": "v2",
        },
        "pages": translated_pages,
    }

    output_path = os.path.join(output_dir, "translated.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"  Translated {len(translated_pages)} pages → {output_path}")
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Translate extracted text (v2)")
    parser.add_argument("input", help="Path to extracted.json")
    parser.add_argument("output_dir", help="Job output directory")
    parser.add_argument("--doc-type", default="general",
                        choices=["legal", "civil", "technical", "auto", "commercial", "general"],
                        help="Document type for glossary selection")
    parser.add_argument("--model", default="claude-sonnet-4-20250514",
                        help="Claude model to use")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    translate_document(data, args.output_dir, doc_type=args.doc_type, model=args.model)
