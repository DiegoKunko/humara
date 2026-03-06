"""Step 1: Extract text blocks and images from PDF preserving layout."""

import json
import os
import fitz  # PyMuPDF


def extract_text_blocks(page):
    """Extract text blocks with font metadata and position from a PDF page."""
    blocks = []
    text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

    for block in text_dict["blocks"]:
        if block["type"] == 0:  # text block
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue
                    blocks.append({
                        "type": "text",
                        "bbox": list(span["bbox"]),
                        "font": span["font"],
                        "size": round(span["size"], 1),
                        "color": f"#{span['color']:06x}",
                        "bold": "bold" in span["font"].lower() or "Bold" in span["font"],
                        "italic": "italic" in span["font"].lower() or "Italic" in span["font"],
                        "text": text,
                    })
    return blocks


def extract_images(page, page_num, images_dir):
    """Extract images from a PDF page and save as JPEG."""
    image_blocks = []
    img_list = page.get_images(full=True)

    for img_idx, img_info in enumerate(img_list):
        xref = img_info[0]
        try:
            base_image = fitz.Pixmap(page.parent, xref)
            if base_image.n > 4:  # CMYK or other, convert to RGB
                base_image = fitz.Pixmap(fitz.csRGB, base_image)

            filename = f"page{page_num:03d}_img{img_idx + 1:02d}.jpeg"
            filepath = os.path.join(images_dir, filename)
            base_image.save(filepath)

            # Try to get image position on page
            img_rects = page.get_image_rects(img_info)
            if img_rects:
                bbox = list(img_rects[0])
            else:
                bbox = [0, 0, base_image.width, base_image.height]

            image_blocks.append({
                "type": "image",
                "bbox": bbox,
                "file": f"images/{filename}",
                "width": base_image.width,
                "height": base_image.height,
            })
        except Exception as e:
            print(f"  Warning: Could not extract image {img_idx + 1} on page {page_num}: {e}")

    return image_blocks


def extract_pdf(pdf_path, output_dir):
    """Extract all text blocks and images from a PDF file.

    Args:
        pdf_path: Path to the input PDF
        output_dir: Job directory to save extracted.json and images/

    Returns:
        dict with metadata and pages array
    """
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        print(f"  Extracting page {page_num + 1}/{len(doc)}...")

        text_blocks = extract_text_blocks(page)
        image_blocks = extract_images(page, page_num + 1, images_dir)

        pages.append({
            "page": page_num + 1,
            "width": page.rect.width,
            "height": page.rect.height,
            "blocks": text_blocks + image_blocks,
        })

    doc.close()

    result = {
        "metadata": {
            "pages": len(pages),
            "source": os.path.basename(pdf_path),
        },
        "pages": pages,
    }

    # Save extracted.json
    output_path = os.path.join(output_dir, "extracted.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"  Extracted {len(pages)} pages → {output_path}")
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python extract.py <pdf_path> <output_dir>")
        sys.exit(1)
    extract_pdf(sys.argv[1], sys.argv[2])
