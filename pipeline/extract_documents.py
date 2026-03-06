"""Universal document extractor: PDF, Word (DOCX), and plain text to pipeline JSON."""

import json
import os
import sys


def extract_pdf(input_path):
    """Extract text blocks from a PDF using PyMuPDF.

    Returns a list of pages, each with blocks containing text and position info.
    """
    import fitz  # PyMuPDF

    doc = fitz.open(input_path)
    pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        rect = page.rect
        blocks_raw = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]

        blocks = []
        for block in blocks_raw:
            if block["type"] == 0:  # Text block
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text:
                            continue
                        bbox = list(span["bbox"])
                        blocks.append({
                            "type": "text",
                            "bbox": [round(b, 1) for b in bbox],
                            "text": text,
                            "size": round(span["size"], 1),
                            "color": "#{:06x}".format(span["color"]),
                            "bold": bool(span["flags"] & 2**4),
                            "italic": bool(span["flags"] & 2**1),
                        })
            elif block["type"] == 1:  # Image block
                blocks.append({
                    "type": "image",
                    "bbox": [round(b, 1) for b in block["bbox"]],
                })

        pages.append({
            "page": page_num + 1,
            "width": round(rect.width, 1),
            "height": round(rect.height, 1),
            "blocks": blocks,
        })

    doc.close()
    return pages


def extract_docx(input_path):
    """Extract text from a Word DOCX file.

    Returns a list with a single 'page' containing all paragraphs as text blocks.
    Since DOCX doesn't have fixed pages, we create logical pages from the content.
    """
    from docx import Document
    from docx.shared import Pt

    doc = Document(input_path)
    blocks = []
    block_index = 0

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        # Detect formatting
        bold = False
        italic = False
        size = 11.0  # default

        if para.runs:
            run = para.runs[0]
            bold = bool(run.bold)
            italic = bool(run.italic)
            if run.font.size:
                size = run.font.size.pt

        # Map paragraph styles to approximate sizes
        style_name = (para.style.name or "").lower()
        if "heading 1" in style_name:
            size = max(size, 16.0)
        elif "heading 2" in style_name:
            size = max(size, 14.0)
        elif "heading 3" in style_name:
            size = max(size, 12.0)
        elif "title" in style_name:
            size = max(size, 20.0)

        # Use a simple vertical layout (no real bbox in DOCX)
        y_pos = block_index * 15.0
        blocks.append({
            "type": "text",
            "bbox": [50.0, y_pos, 550.0, y_pos + 12.0],
            "text": text,
            "size": round(size, 1),
            "color": "#000000",
            "bold": bold,
            "italic": italic,
        })
        block_index += 1

    # Split into logical pages of ~40 blocks each
    page_size = 40
    pages = []
    for i in range(0, len(blocks), page_size):
        page_blocks = blocks[i:i + page_size]
        pages.append({
            "page": (i // page_size) + 1,
            "width": 612.0,
            "height": 792.0,
            "blocks": page_blocks,
        })

    if not pages:
        pages = [{"page": 1, "width": 612.0, "height": 792.0, "blocks": []}]

    return pages


def extract_text(input_path):
    """Extract text from a plain text or markdown file.

    Returns a list with pages of ~40 paragraphs each.
    """
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [line.strip() for line in content.split("\n") if line.strip()]

    blocks = []
    for i, para in enumerate(paragraphs):
        y_pos = i * 15.0
        # Detect headings (markdown-style)
        size = 11.0
        bold = False
        if para.startswith("# "):
            size = 20.0
            bold = True
            para = para[2:]
        elif para.startswith("## "):
            size = 16.0
            bold = True
            para = para[3:]
        elif para.startswith("### "):
            size = 14.0
            bold = True
            para = para[4:]

        blocks.append({
            "type": "text",
            "bbox": [50.0, y_pos, 550.0, y_pos + 12.0],
            "text": para,
            "size": size,
            "color": "#000000",
            "bold": bold,
            "italic": False,
        })

    page_size = 40
    pages = []
    for i in range(0, len(blocks), page_size):
        page_blocks = blocks[i:i + page_size]
        pages.append({
            "page": (i // page_size) + 1,
            "width": 612.0,
            "height": 792.0,
            "blocks": page_blocks,
        })

    if not pages:
        pages = [{"page": 1, "width": 612.0, "height": 792.0, "blocks": []}]

    return pages


def extract_document(input_path, output_dir):
    """Extract text from any supported document format.

    Supported: .pdf, .docx, .txt, .md

    Args:
        input_path: Path to the input document
        output_dir: Directory to save extracted.json

    Returns:
        Dict with metadata and pages
    """
    ext = os.path.splitext(input_path)[1].lower()

    print(f"  Extracting {input_path} (format: {ext})...")

    if ext == ".pdf":
        pages = extract_pdf(input_path)
    elif ext == ".docx":
        pages = extract_docx(input_path)
    elif ext in (".txt", ".md", ".markdown"):
        pages = extract_text(input_path)
    elif ext == ".json":
        # Already extracted — passthrough
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "pages" in data:
            print(f"  JSON passthrough: {len(data['pages'])} pages")
            return data
        else:
            raise ValueError(f"JSON file does not contain 'pages' key: {input_path}")
    else:
        raise ValueError(f"Unsupported file format: {ext}. Supported: .pdf, .docx, .txt, .md, .json")

    total_blocks = sum(len(p["blocks"]) for p in pages)
    text_blocks = sum(1 for p in pages for b in p["blocks"] if b["type"] == "text")

    result = {
        "metadata": {
            "source_file": os.path.basename(input_path),
            "format": ext,
            "total_pages": len(pages),
            "total_blocks": total_blocks,
            "text_blocks": text_blocks,
        },
        "pages": pages,
    }

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "extracted.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"  Extracted {len(pages)} pages ({text_blocks} text blocks) → {output_path}")
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract text from PDF/DOCX/TXT")
    parser.add_argument("input", help="Path to input document (.pdf, .docx, .txt, .md, .json)")
    parser.add_argument("output_dir", help="Output directory for extracted.json")
    args = parser.parse_args()

    extract_document(args.input, args.output_dir)
