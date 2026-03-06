"""Step 4: Rebuild translated PDF — image background + text overlay (v8).

Approach:
1. Each page uses the extracted background IMAGE (graphics, no text) as base.
2. Cleans text: removes ÿ glyph noise, normalizes whitespace.
3. Merges fragmented spans into logical paragraphs with 4 rules:
   a. Bullet/list markers (•, –, -) always start a NEW paragraph
   b. Gap > 1.0× font_size → new paragraph
   c. Font size or color change → new paragraph
   d. Headers (size > 6pt) → never merged with other blocks
4. Expands paragraph bboxes to full column width so Spanish text flows.
5. Expands narrow header bboxes to fit their text.
6. Overlays all text using Arial Unicode (full Unicode: –, •, ¡, ¿, ñ).
"""

import json
import os
import re

import fitz  # PyMuPDF


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

WATERMARKS = [
    "www.carobook.com",
    "traducido automáticamente por google",
    "machine translated by google",
    "translated by google",
]

MIN_FONT_SIZE = 1.0
GLYPH_NOISE_RE = re.compile(r'^[\s\u00ff]+$')
MAX_BLOCK_AREA_RATIO = 0.25

# Font — Arial Unicode MS supports full Unicode
FONT_PATH = "/Library/Fonts/Arial Unicode.ttf"
FONT_NAME = "aruni"

# Merging thresholds
SAME_LINE_Y_THRESH = 3.0   # pts — blocks within this Y-gap are on the same line
PARA_GAP_FACTOR   = 1.0    # merge lines if gap < factor × font_size (lower = less aggressive)
COLUMN_X_FRACTION = 0.52   # initial left/right split (refined dynamically)

# Bullet/list marker — these always start a new paragraph
BULLET_RE = re.compile(r'^[•–\-►▸■◆]\s|^[•–]$|^\d+[\.\)]\s|^ADVERTENCIA|^Aviso')

# Header font size threshold
HEADER_SIZE_THRESH = 6.0

# Approximate character width coefficient (Arial Unicode)
CHAR_WIDTH_COEFF = 0.55


# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------

def clean_text(text):
    """Strip ÿ (U+00FF) placeholders and normalize whitespace."""
    text = text.replace('\u00ff', '')
    text = re.sub(r'  +', ' ', text)
    return text.strip()


def is_watermark(text):
    return any(wm in text.strip().lower() for wm in WATERMARKS)


def is_noise(block):
    if block["size"] < MIN_FONT_SIZE:
        return True
    text = block["text"].strip()
    if not text or GLYPH_NOISE_RE.match(text):
        return True
    return False


def is_page_number(block, pw, ph):
    """Detect lone page-number blocks (tiny numbered box near margin)."""
    text = clean_text(block["text"])
    if not text or not text.isdigit() or len(text) > 3:
        return False
    bw = block["bbox"][2] - block["bbox"][0]
    return bw < 10 and block["size"] < 6


def starts_new_paragraph(text):
    """True if the text begins a new list item / warning label."""
    return bool(BULLET_RE.match(text))


# ---------------------------------------------------------------------------
# Column detection
# ---------------------------------------------------------------------------

def detect_columns(blocks, pw):
    """Detect left/right column x-boundaries from block x-coordinates.

    Returns (left_x0, left_x1, right_x0, right_x1) or None if single-column.
    """
    # Collect x-start positions of substantial text blocks
    xs = []
    for b in blocks:
        if b["type"] != "text" or b["size"] < 1.5:
            continue
        text = clean_text(b["text"])
        if not text or is_watermark(b["text"]):
            continue
        xs.append(b["bbox"][0])

    if not xs:
        margin = pw * 0.10
        return (margin, pw / 2 - 5, pw / 2 + 5, pw - margin)

    # Find the natural gap between left and right column starts
    # Most left-column blocks start at ~45pt, right-column at ~233pt on 419pt pages.
    left_starts  = sorted(x for x in xs if x < pw * 0.40)
    right_starts = sorted(x for x in xs if x >= pw * 0.40)

    l_x0 = min(left_starts)  if left_starts  else pw * 0.05
    r_x0 = min(right_starts) if right_starts else pw * 0.52

    # Right edge of each column: maximum x1 of blocks in that column
    l_x1 = max(
        (b["bbox"][2] for b in blocks
         if b["type"] == "text" and b["bbox"][0] < pw * 0.52),
        default=pw * 0.50,
    )
    r_x1 = max(
        (b["bbox"][2] for b in blocks
         if b["type"] == "text" and b["bbox"][0] >= pw * 0.40),
        default=pw * 0.95,
    )
    # Clamp to page
    l_x1 = min(l_x1, pw - 5)
    r_x1 = min(r_x1, pw - 5)

    return (l_x0, l_x1, r_x0, r_x1)


# ---------------------------------------------------------------------------
# Block merging
# ---------------------------------------------------------------------------

def merge_text_blocks(blocks, pw, ph):
    """Merge fragmented text spans into logical paragraphs.

    Steps:
    0. Filter noise / watermarks / page numbers
    1. Group blocks on the same line (same Y within threshold)
    2. Merge horizontally within each line, separated by column
    3. Merge consecutive same-column lines → paragraphs (smart rules)
    4. Expand paragraph bboxes to full column width + vertical space
    """
    # --- Step 0: Filter ---
    valid = []
    for b in blocks:
        if b["type"] != "text":
            continue
        if is_noise(b) or is_watermark(b["text"]):
            continue
        if is_page_number(b, pw, ph):
            continue
        text = clean_text(b["text"])
        if not text:
            continue
        valid.append({
            "bbox": list(b["bbox"]),
            "text": text,
            "size": b["size"],
            "color": b["color"],
            "bold": b.get("bold", False),
            "italic": b.get("italic", False),
        })

    if not valid:
        return []

    # Detect column layout for this page
    col_l_x0, col_l_x1, col_r_x0, col_r_x1 = detect_columns(blocks, pw)
    col_split_x = pw * COLUMN_X_FRACTION

    # --- Step 1: Group into lines (same Y) ---
    valid.sort(key=lambda b: (round(b["bbox"][1] / SAME_LINE_Y_THRESH),
                               b["bbox"][0]))
    lines = []
    cur_line = [valid[0]]
    for b in valid[1:]:
        if abs(b["bbox"][1] - cur_line[0]["bbox"][1]) <= SAME_LINE_Y_THRESH:
            cur_line.append(b)
        else:
            lines.append(cur_line)
            cur_line = [b]
    lines.append(cur_line)

    # --- Step 2: Merge horizontally per column ---
    merged_lines = []
    for line in lines:
        line.sort(key=lambda b: b["bbox"][0])
        left  = [b for b in line if (b["bbox"][0] + b["bbox"][2]) / 2 <  col_split_x]
        right = [b for b in line if (b["bbox"][0] + b["bbox"][2]) / 2 >= col_split_x]

        for col_blocks in (left, right):
            if not col_blocks:
                continue
            text = " ".join(b["text"] for b in col_blocks)
            text = re.sub(r'  +', ' ', text).strip()
            if not text:
                continue
            x0 = min(b["bbox"][0] for b in col_blocks)
            y0 = min(b["bbox"][1] for b in col_blocks)
            x1 = max(b["bbox"][2] for b in col_blocks)
            y1 = max(b["bbox"][3] for b in col_blocks)
            merged_lines.append({
                "bbox": [x0, y0, x1, y1],
                "text": text,
                "size": col_blocks[0]["size"],
                "color": col_blocks[0]["color"],
                "bold": col_blocks[0].get("bold", False),
                "italic": col_blocks[0].get("italic", False),
            })

    if not merged_lines:
        return []

    # --- Step 3: Merge consecutive lines → paragraphs (per column) ---
    left_lines  = sorted(
        [m for m in merged_lines if (m["bbox"][0] + m["bbox"][2]) / 2 <  col_split_x],
        key=lambda b: b["bbox"][1],
    )
    right_lines = sorted(
        [m for m in merged_lines if (m["bbox"][0] + m["bbox"][2]) / 2 >= col_split_x],
        key=lambda b: b["bbox"][1],
    )

    paragraphs = []
    for column in (left_lines, right_lines):
        if not column:
            continue
        cur_para = [column[0]]

        for m in column[1:]:
            prev = cur_para[-1]

            # Rule A: bullet/list markers always start a new paragraph
            if starts_new_paragraph(m["text"]):
                paragraphs.append(cur_para)
                cur_para = [m]
                continue

            # Rule B: headers never merge with adjacent blocks
            if prev["size"] > HEADER_SIZE_THRESH or m["size"] > HEADER_SIZE_THRESH:
                paragraphs.append(cur_para)
                cur_para = [m]
                continue

            # Rule C: gap > threshold → new paragraph
            y_gap   = m["bbox"][1] - prev["bbox"][3]
            max_gap = prev["size"] * PARA_GAP_FACTOR
            if y_gap > max_gap or y_gap < 0:
                paragraphs.append(cur_para)
                cur_para = [m]
                continue

            # Rule D: font size or color change → new paragraph
            if (abs(m["size"] - prev["size"]) >= 1.0
                    or m["color"] != prev["color"]):
                paragraphs.append(cur_para)
                cur_para = [m]
                continue

            # Passed all checks → continuation line, merge
            cur_para.append(m)

        paragraphs.append(cur_para)

    # --- Step 4: Build paragraph blocks + expand bboxes ---
    result = []
    for para in paragraphs:
        text = " ".join(m["text"] for m in para)
        text = re.sub(r'  +', ' ', text).strip()
        if not text:
            continue

        # Raw union bbox
        x0 = min(m["bbox"][0] for m in para)
        y0 = min(m["bbox"][1] for m in para)
        x1 = max(m["bbox"][2] for m in para)
        y1 = max(m["bbox"][3] for m in para)

        size  = para[0]["size"]
        color = para[0]["color"]

        # Expand x to full column width so longer Spanish text has room
        cx = (x0 + x1) / 2
        if cx < col_split_x:
            # Left column
            x0 = col_l_x0
            x1 = col_l_x1
        else:
            # Right column
            x0 = col_r_x0
            x1 = col_r_x1

        # For headers that are narrower than the text they need to show,
        # ensure at least enough width: estimated width = chars × size × coeff
        if size > HEADER_SIZE_THRESH:
            est_w = len(text) * size * CHAR_WIDTH_COEFF
            if est_w > (x1 - x0):
                x1 = min(x0 + est_w * 1.1, pw - 5)
            # Ensure minimum height for one line
            min_h = size * 1.5
            if (y1 - y0) < min_h:
                y1 = y0 + min_h

        result.append({
            "bbox": [x0, y0, x1, y1],
            "text": text,
            "size": size,
            "color": color,
            "bold": para[0].get("bold", False),
            "italic": para[0].get("italic", False),
        })

    # Expand each paragraph's y1 to the next paragraph's y0
    # so text has full vertical space to flow without cutting off
    result.sort(key=lambda b: (b["bbox"][0], b["bbox"][1]))
    for i, para in enumerate(result):
        # Find the next para in the same column
        cx = (para["bbox"][0] + para["bbox"][2]) / 2
        next_y = None
        for j in range(i + 1, len(result)):
            nx = (result[j]["bbox"][0] + result[j]["bbox"][2]) / 2
            if abs(nx - cx) < pw * 0.20 and result[j]["bbox"][1] > para["bbox"][3]:
                next_y = result[j]["bbox"][1]
                break
        if next_y is not None:
            para["bbox"][3] = next_y - 1

    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def hex_to_color(hex_str):
    """'#RRGGBB' → (R/255, G/255, B/255)."""
    h = hex_str.lstrip('#')
    return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))


def insert_text_fitted(page, rect, text, fontsize, color):
    """Insert text with progressive font scaling until it fits."""
    for scale in [1.0, 0.92, 0.84, 0.76, 0.68, 0.60, 0.52, 0.44]:
        fs = max(fontsize * scale, 1.2)
        rc = page.insert_textbox(
            rect, text,
            fontsize=fs,
            fontname=FONT_NAME,
            fontfile=FONT_PATH,
            color=color,
            align=fitz.TEXT_ALIGN_LEFT,
        )
        if rc >= 0:
            return True, scale
    return False, 0


# ---------------------------------------------------------------------------
# Main rebuild
# ---------------------------------------------------------------------------

def rebuild_document(proofread_data, job_dir):
    input_pdf  = os.path.join(job_dir, "input.pdf")
    output_pdf = os.path.join(job_dir, "output.pdf")
    images_dir = os.path.join(job_dir, "images")

    if not os.path.exists(input_pdf):
        print(f"  Error: {input_pdf} not found")
        return None

    orig_doc   = fitz.open(input_pdf)
    pages_data = proofread_data["pages"]
    num_pages  = min(len(orig_doc), len(pages_data))

    doc = fitz.open()  # new document

    total_blocks   = 0
    total_overflow = 0
    total_scaled   = 0

    print(f"  Processing {num_pages} pages...")

    for page_idx in range(num_pages):
        page_data = pages_data[page_idx]
        pw = page_data.get("width",  orig_doc[page_idx].rect.width)
        ph = page_data.get("height", orig_doc[page_idx].rect.height)

        # Create blank page
        page = doc.new_page(width=pw, height=ph)

        # Background: extracted page image (graphics only, no text)
        img_path = os.path.join(images_dir, f"page{page_idx+1:03d}_img01.jpeg")
        if os.path.exists(img_path):
            page.insert_image(fitz.Rect(0, 0, pw, ph), filename=img_path)
        else:
            page.show_pdf_page(page.rect, orig_doc, page_idx)

        # Merge blocks → paragraphs
        merged = merge_text_blocks(page_data["blocks"], pw, ph)

        # Insert each paragraph
        for block in merged:
            rect = fitz.Rect(block["bbox"])

            if rect.width * rect.height / (pw * ph) > MAX_BLOCK_AREA_RATIO:
                continue
            rect.intersect(page.rect)
            if rect.is_empty or rect.width < 2 or rect.height < 2:
                continue

            text = block["text"]
            if not text:
                continue

            color   = hex_to_color(block["color"])
            fitted, scale = insert_text_fitted(
                page, rect, text, block["size"], color
            )
            total_blocks += 1
            if not fitted:
                total_overflow += 1
            elif scale < 1.0:
                total_scaled += 1

        if (page_idx + 1) % 25 == 0 or page_idx == num_pages - 1:
            print(f"    Page {page_idx + 1}/{num_pages}...")

    orig_doc.close()
    doc.save(output_pdf, garbage=4, deflate=True)
    doc.close()

    print(f"  {total_blocks} paragraphs inserted, "
          f"{total_scaled} scaled down, {total_overflow} overflow")
    print(f"  PDF \u2192 {output_pdf}")
    return output_pdf


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python rebuild.py <proofread.json> <job_dir>")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        d = json.load(f)
    rebuild_document(d, sys.argv[2])
