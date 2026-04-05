"""Step 1 (OCR): Extract text from scanned PDFs using Claude Vision.

For scanned documents where PyMuPDF finds no text blocks, this module
converts each page to an image and uses Claude's vision to extract text
with layout information.

Usage:
    python extract_ocr.py <pdf_path> <output_dir>
"""

import base64
import json
import os
import sys
import time

import anthropic
import fitz  # PyMuPDF


def pdf_page_to_base64(doc, page_num, dpi=200):
    """Render a PDF page to a base64-encoded JPEG."""
    page = doc[page_num]
    # Render at higher DPI for better OCR quality
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("jpeg", jpg_quality=90)
    return base64.standard_b64encode(img_bytes).decode("utf-8")


def extract_page_text(client, image_b64, page_num, total_pages,
                      model="claude-sonnet-4-20250514"):
    """Use Claude Vision to extract text blocks from a scanned page image."""
    system_prompt = """Eres un sistema OCR de alta precisión para documentos legales escaneados.

Tu tarea es extraer TODO el texto visible en la imagen de forma precisa y estructurada.

REGLAS:
1. Extrae CADA línea de texto visible, exactamente como aparece
2. Preserva mayúsculas, puntuación, números, y formato original
3. Los nombres propios deben ser EXACTOS (personas, empresas, lugares)
4. Los números, fechas, y referencias deben ser EXACTOS
5. Si hay una tabla, extrae cada celda como un bloque separado
6. Si hay texto manuscrito o firmas, indica [firma] o [texto manuscrito ilegible]
7. Si hay sellos, indica [sello: descripción breve]
8. NO traduzcas nada — extrae el texto en su idioma original
9. NO interpretes ni corrijas el texto — transcríbelo tal cual
10. Agrupa el texto en bloques lógicos (párrafos, títulos, items de lista)

Devuelve EXCLUSIVAMENTE un JSON válido con esta estructura:
[
  {
    "block_id": 1,
    "text": "texto extraído exacto",
    "type": "title|heading|paragraph|list_item|table_cell|signature|seal|page_number|reference",
    "bold": true/false,
    "position": "top|middle|bottom"
  }
]

NO incluir markdown, ni ```, ni explicaciones fuera del JSON."""

    response = client.messages.create(
        model=model,
        max_tokens=8192,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_b64,
                    },
                },
                {
                    "type": "text",
                    "text": f"Extrae todo el texto de esta imagen (página {page_num}/{total_pages} de un documento legal corporativo). Devuelve JSON.",
                },
            ],
        }],
    )

    response_text = response.content[0].text
    # Strip markdown code fences if present
    if response_text.startswith("```"):
        first_nl = response_text.index("\n")
        response_text = response_text[first_nl + 1:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

    return json.loads(response_text)


def extract_pdf_ocr(pdf_path, output_dir, model="claude-sonnet-4-20250514"):
    """Extract text from a scanned PDF using Claude Vision OCR.

    Args:
        pdf_path: Path to the input PDF
        output_dir: Job directory to save extracted.json and images/

    Returns:
        dict with metadata and pages array (same format as extract.py)
    """
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    client = anthropic.Anthropic()
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    pages = []

    print(f"  OCR extracting {total_pages} pages with Claude Vision...")

    for page_num in range(total_pages):
        page = doc[page_num]
        pw = page.rect.width
        ph = page.rect.height

        print(f"  Page {page_num + 1}/{total_pages}...", end=" ", flush=True)

        # Save page image for rebuild step
        zoom = 200 / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img_path = os.path.join(images_dir, f"page{page_num + 1:03d}_img01.jpeg")
        pix.save(img_path)

        # Get base64 for Claude Vision
        image_b64 = base64.standard_b64encode(pix.tobytes("jpeg", jpg_quality=90)).decode("utf-8")

        try:
            ocr_blocks = extract_page_text(
                client, image_b64, page_num + 1, total_pages, model=model
            )

            # Convert OCR blocks to the standard extract format
            blocks = []
            y_cursor = 50  # Start Y position
            line_height = 14

            for ob in ocr_blocks:
                text = ob.get("text", "").strip()
                if not text:
                    continue

                # Estimate font size based on type
                block_type = ob.get("type", "paragraph")
                if block_type == "title":
                    font_size = 16.0
                    is_bold = True
                elif block_type == "heading":
                    font_size = 12.0
                    is_bold = True
                elif block_type in ("signature", "seal"):
                    font_size = 10.0
                    is_bold = False
                elif block_type == "page_number":
                    font_size = 8.0
                    is_bold = False
                else:
                    font_size = 10.0
                    is_bold = ob.get("bold", False)

                # Estimate bbox based on position and text length
                est_width = min(len(text) * font_size * 0.5, pw - 80)
                x0 = 40
                x1 = x0 + est_width
                y0 = y_cursor
                y1 = y0 + font_size * 1.4 * max(1, len(text) // 80 + 1)

                blocks.append({
                    "type": "text",
                    "bbox": [x0, y0, x1, y1],
                    "font": "scan-ocr",
                    "size": font_size,
                    "color": "#000000",
                    "bold": is_bold,
                    "italic": False,
                    "text": text,
                })

                y_cursor = y1 + 4

            # Add image block
            blocks.append({
                "type": "image",
                "bbox": [0, 0, pix.width, pix.height],
                "file": f"images/page{page_num + 1:03d}_img01.jpeg",
                "width": pix.width,
                "height": pix.height,
            })

            pages.append({
                "page": page_num + 1,
                "width": pw,
                "height": ph,
                "blocks": blocks,
            })

            text_count = len([b for b in blocks if b["type"] == "text"])
            print(f"→ {text_count} text blocks")

        except Exception as e:
            print(f"ERROR: {e}")
            # Add page with just the image
            pages.append({
                "page": page_num + 1,
                "width": pw,
                "height": ph,
                "blocks": [{
                    "type": "image",
                    "bbox": [0, 0, pix.width, pix.height],
                    "file": f"images/page{page_num + 1:03d}_img01.jpeg",
                    "width": pix.width,
                    "height": pix.height,
                }],
            })

        # Rate limiting
        if page_num < total_pages - 1:
            time.sleep(0.5)

    doc.close()

    result = {
        "metadata": {
            "pages": len(pages),
            "source": os.path.basename(pdf_path),
            "ocr": True,
            "ocr_model": model,
        },
        "pages": pages,
    }

    # Save extracted.json
    output_path = os.path.join(output_dir, "extracted.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    total_text_blocks = sum(
        1 for p in pages for b in p["blocks"] if b["type"] == "text"
    )
    print(f"  OCR complete: {len(pages)} pages, {total_text_blocks} text blocks → {output_path}")
    return result


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python extract_ocr.py <pdf_path> <output_dir>")
        sys.exit(1)
    extract_pdf_ocr(sys.argv[1], sys.argv[2])
