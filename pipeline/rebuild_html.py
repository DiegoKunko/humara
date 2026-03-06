#!/usr/bin/env python3
"""rebuild_html.py: Genera PDF traducido usando template HTML + texto semántico.

v3 — Cambios clave:
- merge_column_blocks(): une fragmentos de línea en párrafos completos
- Separación correcta de 2 columnas
- CSS con colores explícitos (sin var()) para weasyprint
- Imágenes con caption debajo

Uso: python rebuild_html.py <proofread.json> <job_dir> [--pages 29-31]
"""

import html as _html
import json
import os
import re
import sys

try:
    from PIL import Image as _PILImage
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ---------------------------------------------------------------------------
# CSS — colores explícitos (no var()) para máxima compatibilidad con weasyprint
# ---------------------------------------------------------------------------

CSS = """
/* Pantalla: contenedor tipo documento */
@media screen {
  body {
    background: #e8e8e8;
    padding: 30px 0;
  }
  .page-container {
    background: #ffffff;
    max-width: 820px;
    margin: 0 auto;
    padding: 30pt 36pt;
    box-shadow: 0 2px 16px rgba(0,0,0,0.18);
    border-radius: 3px;
  }
}
/* PDF: sin restricción de ancho */
@media print {
  .page-container { padding: 0; }
}

body {
  font-family: 'Helvetica Neue', Arial, sans-serif;
  font-size: 9pt;
  line-height: 1.45;
  color: #1A1A1A;
  margin: 0;
  padding: 0;
}

@page {
  size: A4;
  margin: 14mm 16mm 16mm 16mm;
  @bottom-center {
    content: counter(page);
    font-family: Arial, sans-serif;
    font-size: 7pt;
    color: #aaa;
  }
}

* { margin: 0; padding: 0; box-sizing: border-box; }

/* ── Chapter title (grande, azul VW) ── */
h1.chapter-title {
  font-size: 16pt;
  font-weight: bold;
  color: #0066B3;
  margin: 0 0 6pt 0;
  padding-bottom: 4pt;
  border-bottom: 2pt solid #0066B3;
  page-break-before: always;
}
h1.chapter-title:first-child { page-break-before: avoid; }

/* ── Section header (barra azul oscura, texto blanco) ── */
.section-header {
  background: #2B3D52;
  color: #ffffff;
  padding: 5pt 10pt;
  border-radius: 3pt;
  margin: 8pt 0 4pt 0;
  font-size: 9.5pt;
  font-weight: bold;
  display: block;
}

/* ── Topic header (barra pequeña azul oscura, texto blanco) ── */
.topic-header {
  background: #2B3D52;
  color: #ffffff;
  padding: 3pt 10pt;
  border-radius: 3pt;
  margin: 6pt 0 3pt 0;
  font-size: 8.5pt;
  font-weight: bold;
  display: block;
}

/* ── Subsection (texto azul subrayado) ── */
.subsection {
  font-size: 9pt;
  font-weight: bold;
  color: #0066B3;
  margin: 6pt 0 2pt 0;
  padding-bottom: 2pt;
  border-bottom: 0.5pt solid #E0E0E0;
}

/* ── Body paragraph ── */
p {
  margin: 3pt 0;
  line-height: 1.45;
  orphans: 2;
  widows: 2;
}

/* ── Bullet list ── */
ul {
  margin: 2pt 0 4pt 16pt;
  padding: 0;
}
li {
  margin: 2pt 0;
  line-height: 1.4;
}

/* ── ADVERTENCIA box (naranja) ── */
.warn-box {
  background: #FFF4E6;
  border-left: 3pt solid #D4650A;
  border-radius: 3pt;
  padding: 6pt 10pt;
  margin: 6pt 0;
  page-break-inside: avoid;
}
.warn-box .alert-header {
  color: #D4650A;
  font-weight: bold;
  font-size: 9pt;
  text-transform: uppercase;
  letter-spacing: 0.2pt;
  margin-bottom: 3pt;
  display: flex;
  align-items: center;
  gap: 5pt;
}
.warn-box .alert-icon { font-size: 11pt; }
.warn-box .alert-content { font-size: 8.5pt; line-height: 1.4; }
.warn-box .alert-content p { margin: 2pt 0; }

/* ── AVISO box (azul) ── */
.hint-box {
  background: #E8F4FD;
  border-left: 3pt solid #0078D4;
  border-radius: 3pt;
  padding: 6pt 10pt;
  margin: 6pt 0;
  page-break-inside: avoid;
}
.hint-box .alert-header {
  color: #0078D4;
  font-weight: bold;
  font-size: 9pt;
  letter-spacing: 0.2pt;
  margin-bottom: 3pt;
  display: flex;
  align-items: center;
  gap: 5pt;
}
.hint-box .alert-icon { font-size: 11pt; }
.hint-box .alert-content { font-size: 8.5pt; line-height: 1.4; }
.hint-box .alert-content p { margin: 2pt 0; }

/* ── NOTA box (verde) ── */
.note-box {
  background: #F1F8E9;
  border-left: 3pt solid #2E7D32;
  border-radius: 3pt;
  padding: 6pt 10pt;
  margin: 6pt 0;
  page-break-inside: avoid;
}
.note-box .alert-header {
  color: #2E7D32;
  font-weight: bold;
  font-size: 9pt;
  margin-bottom: 3pt;
  display: flex;
  align-items: center;
  gap: 5pt;
}
.note-box .alert-icon { font-size: 11pt; }
.note-box .alert-content { font-size: 8.5pt; line-height: 1.4; }
.note-box .alert-content p { margin: 2pt 0; }

/* ── Figures / images ── */
.figure {
  margin: 6pt 0;
  text-align: center;
  page-break-inside: avoid;
}
.figure img {
  max-width: 88%;
  height: auto;
  border: 0.5pt solid #E0E0E0;
  border-radius: 2pt;
}
.figure-caption {
  font-size: 7.5pt;
  color: #666666;
  margin-top: 3pt;
  font-style: italic;
  text-align: center;
}

/* ── Cross-reference ── */
.cross-ref {
  color: #0066B3;
  font-size: 8pt;
  margin: 2pt 0;
  font-style: italic;
}

/* ── Page separator (sutil) ── */
.page-sep {
  color: #dddddd;
  font-size: 6.5pt;
  text-align: right;
  margin: 5pt 0 2pt 0;
  border-top: 0.5pt solid #eeeeee;
  padding-top: 2pt;
}

/* ── Two-column layout (display:table para weasyprint) ── */
.two-col {
  display: table;
  width: 100%;
  table-layout: fixed;
  margin: 8pt 0;
}
.col-left {
  display: table-cell;
  width: 50%;
  vertical-align: top;
  padding-right: 10pt;
}
.col-right {
  display: table-cell;
  width: 50%;
  vertical-align: top;
  padding-left: 10pt;
  border-left: 0.5pt solid #eeeeee;
}

/* ── Warning light table ── */
.warn-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 8.5pt;
  margin: 6pt 0 10pt 0;
  page-break-inside: avoid;
}
.warn-table th {
  background: #E0E0E0;
  padding: 4pt 6pt;
  text-align: left;
  font-weight: bold;
  border: 0.5pt solid #cccccc;
}
.warn-table td {
  padding: 4pt 6pt;
  vertical-align: top;
  border: 0.5pt solid #dddddd;
  line-height: 1.5;
}
.warn-table tr:nth-child(even) td { background: #F9F9F9; }

/* ── Topic break between sections ── */
.topic-break { page-break-before: always; }
"""

HTML_DOC = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>VW ID.6 X — Manual (traducción)</title>
<style>{css}</style>
</head>
<body>
<div class="page-container">
{body}
</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

WATERMARKS = [
    "www.carobook.com",
    "traducido automáticamente por google",
    "traducido por google",
    "machine translated by google",
    "translated by google",
]

def clean(text: str) -> str:
    text = text.replace('\u00ff', '')
    text = re.sub(r'  +', ' ', text)
    return text.strip()

FOOTER_RE = re.compile(r'^(Seguridad|Safety|Sicherheit)\s+\d+$', re.I)

def is_skip(b: dict) -> bool:
    t = clean(b.get('text', ''))
    if not t or b.get('size', 0) < 1.5:
        return True
    if any(w in t.lower() for w in WATERMARKS):
        return True
    # Número de página suelto
    if t.isdigit() and len(t) <= 3 and b.get('size', 99) < 6:
        return True
    # Flecha sola (referencia vacía)
    if t in ('→', '←', '↑', '↓', '▶'):
        return True
    # Footer del PDF original ("Seguridad 29", etc.)
    if FOOTER_RE.match(t):
        return True
    # Texto en gris footer (#828f96)
    if b.get('color', '') == '#828f96':
        return True
    # Fragmentos cortos en rojo (highlights del PDF original, ej. "se", "ÿ")
    if b.get('color', '') == '#ee1d23' and len(t) <= 4:
        return True
    # Referencia inline "Fig. N." sola (no es caption real, solo cross-ref)
    if re.match(r'^Fig\.\s*\d+\.?$', t):
        return True
    # Referencia inline "Figura N." sola (sin descripción = no es caption real)
    if re.match(r'^Figura\s+\d+\.?\s*$', t, re.I):
        return True
    # "Fig." solo sin número — fragmento o cross-ref suelto
    if re.match(r'^Fig\.?\s*$', t):
        return True
    # Labels standalone de cajas de advertencia (extraídos como bloque de texto suelto)
    # "warn", "advertencia", "peligro", etc. aparecen a tamaño grande como etiquetas gráficas
    if (len(t.split()) == 1
            and t.lower() in ('warn', 'warning', 'advertencia', 'advertissement',
                               'achtung', 'peligro', 'danger', 'checklist')
            and b.get('size', 0) >= 5.0):
        return True
    return False

def esc(text: str) -> str:
    return _html.escape(text)


# ---------------------------------------------------------------------------
# Block merging — une fragmentos de línea en unidades semánticas completas
# ---------------------------------------------------------------------------

BULLET_START = re.compile(r'^[•►▸■◆]\s*|^[–\-]\s+')
HEADER_COLORS = ('#0160ae', '#0066b3', '#0066B3')

def _combine(blocks: list) -> dict:
    """Une una lista de bloques en uno solo."""
    if len(blocks) == 1:
        return dict(blocks[0])
    text = ' '.join(clean(b.get('text', '')) for b in blocks)
    text = re.sub(r'  +', ' ', text).strip()
    return {
        'bbox': [
            min(b['bbox'][0] for b in blocks),
            min(b['bbox'][1] for b in blocks),
            max(b['bbox'][2] for b in blocks),
            max(b['bbox'][3] for b in blocks),
        ],
        'text':  text,
        'size':  blocks[0].get('size', 0),
        'color': blocks[0].get('color', '#000000'),
        'bold':  blocks[0].get('bold', False),
        'italic':blocks[0].get('italic', False),
        'type':  'text',
    }

def merge_column_blocks(blocks: list) -> list:
    """Une bloques fragmentados dentro de una columna en párrafos/ítems completos.

    Reglas de corte (nuevo grupo):
    - Texto blanco (#ffffff): siempre standalone (header bar)
    - Size ≥ 7pt: siempre standalone (warning/section header)
    - Nuevo bullet marker (•, –): siempre inicia nuevo ítem
    - Cambio de color o tamaño significativo (≥1pt)
    - Gap vertical > 2.5× font_size (salto de párrafo/sección)
    """
    if not blocks:
        return []

    result = []
    group  = [blocks[0]]

    for b in blocks[1:]:
        prev = group[-1]
        t        = clean(b.get('text', ''))
        b_size   = b.get('size', 0)
        b_color  = b.get('color', '#000000')
        p_size   = prev.get('size', 0)
        p_color  = prev.get('color', '#000000')
        y_gap    = b['bbox'][1] - prev['bbox'][3]

        split = (
            b_color == '#ffffff'                        or  # nuevo header
            p_color == '#ffffff'                        or  # prev era header
            b_size  >= 7.0                              or  # warning / section header
            p_size  >= 7.0                              or  # prev era warning / section
            (b_size >= 9 and b_color in HEADER_COLORS)  or  # chapter title
            bool(BULLET_START.match(t))                 or  # nuevo bullet
            b_color != p_color                          or  # color distinto
            abs(b_size - p_size) >= 1.0                 or  # tamaño distinto
            y_gap   > p_size * 2.5                      or  # salto de párrafo
            (y_gap  < -1.0 and b['bbox'][1] < prev['bbox'][1] - 0.5)  # solapamiento real
        )

        if split:
            result.append(_combine(group))
            group = [b]
        else:
            group.append(b)

    result.append(_combine(group))
    return result


# ---------------------------------------------------------------------------
# Clasificador de bloques
# ---------------------------------------------------------------------------

WARN_RE  = re.compile(r'^ADVERTENCIA\b|^Advertencia\b|^advertir\b', re.I)
HINT_RE  = re.compile(r'^Aviso\b|^Consejo\b|^Sugerencia\b', re.I)
NOTE_RE  = re.compile(r'^Nota\b|^nota\b|^Observa\b')
FIG_RE   = re.compile(r'^(Figura\s+\d|Fig\.\s*\d|BTT[-–]\d)', re.I)
ARROW_RE = re.compile(r'^→')

CROSSREF_PAGE_RE = re.compile(r'^Nota en la página\s+\d', re.I)

def classify(b: dict) -> str:
    # Pseudo-bloques inyectados
    if b.get('type') == 'figure_image':
        return 'figure_image'
    if b.get('type') == 'raw_html':
        return 'raw_html'

    t     = clean(b.get('text', ''))
    size  = b.get('size', 0)
    color = b.get('color', '#000000')

    # Cross-ref de página ("Nota en la página 27 al inicio...")
    if CROSSREF_PAGE_RE.match(t):
        return 'cross_ref'

    # 1. Texto blanco en barra oscura → topic_header
    if color == '#ffffff' and size >= 4.0:
        return 'topic_header'

    # 2. Título de capítulo (azul VW, grande)
    if size >= 9 and color in HEADER_COLORS:
        return 'chapter_title'

    # 3. Warnings/hints — ANTES de size-based headers
    #    Solo si size ≥ 7 (headers reales son ~8pt; body que menciona "ADVERTENCIA" es ~4.7pt)
    if size >= 7.0 and WARN_RE.match(t):
        return 'warning'
    if size >= 7.0 and HINT_RE.match(t):
        return 'hint'
    # NOTE: solo si es una etiqueta standalone, NO "Nota en la página X" (cross-ref)
    if size >= 5.0 and NOTE_RE.match(t) and len(t) < 60 and 'página' not in t.lower():
        return 'note'

    # 4. Headers por tamaño — solo si bold o color de header (no para body en tamaño grande)
    if size >= 7.5 and (b.get('bold', False) or color in HEADER_COLORS):
        return 'section_header'
    if size >= 6.0 and (b.get('bold', False) or color in HEADER_COLORS):
        return 'subsection'

    # 5. Caption de figura
    if FIG_RE.match(t):
        # Cross-ref multi-figura: "Figura 27 Figura 28, y no se deben..." → body, no caption
        if re.match(r'^Figura\s+\d+\s+(Figura|Fig\.)', t, re.I):
            return 'body'
        return 'figure_caption'

    # 6. Referencia cruzada
    if ARROW_RE.match(t):
        return 'cross_ref'

    # 7. Texto azul VW (callout/hint no etiquetado explícitamente)
    # Requiere al menos 4 palabras para evitar clasificar fragmentos cortos como hint
    if color in HEADER_COLORS and size >= 4.0 and len(t.split()) >= 4:
        return 'hint'

    # 8. Ítem de lista
    if BULLET_START.match(t):
        return 'bullet'

    return 'body'


# ---------------------------------------------------------------------------
# Renderizador de una columna → lista de HTML parts
# ---------------------------------------------------------------------------

def render_blocks(col_blocks: list) -> list:
    """Convierte una lista de bloques semánticos a HTML parts."""
    parts     = []
    in_list   = False
    pending   = None   # {'type': warn|hint|note, 'title': str, 'items': [str]}
    last_text = None

    def flush_list():
        nonlocal in_list
        if in_list:
            parts.append('</ul>')
            in_list = False

    def flush_alert():
        nonlocal pending
        if not pending:
            return
        atype = pending['type']
        title = esc(pending['title'])
        items = pending['items']
        css   = f'{atype}-box'
        icon  = '⚠' if atype == 'warn' else ('ℹ' if atype == 'hint' else '📝')
        content_html = '\n'.join(f'<p>{esc(x)}</p>' for x in items) if items else ''
        parts.append(
            f'<div class="{css}">'
            f'<div class="alert-header">'
            f'<span class="alert-icon">{icon}</span>'
            f'<span>{title}</span>'
            f'</div>'
            f'<div class="alert-content">{content_html}</div>'
            f'</div>'
        )
        pending = None

    def emit(b):
        nonlocal in_list, pending, last_text

        t    = clean(b.get('text', ''))
        role = classify(b)

        # Skip duplicados exactos consecutivos
        if t == last_text:
            return
        last_text = t

        # ⚠ símbolo suelto (artefacto de extracción del PDF)
        if t in ('⚠', '⚠️', '!'):
            return

        # Contenido dentro de un alert box abierto
        if pending and role in ('body', 'bullet', 'cross_ref', 'figure_caption'):
            item = BULLET_START.sub('', t).strip()
            if item:
                # Separar bullets embebidos dentro de texto fusionado ("A. • B." → ["A.", "B."])
                sub_items = re.split(r'\s*[•►▸■◆]\s+', item)
                for sub in sub_items:
                    if sub.strip():
                        pending['items'].append(sub.strip())
            return
        elif pending and role not in ('warning', 'hint', 'note'):
            flush_alert()
            # figure_image y raw_html siempre cierran el alert antes de renderizar

        if role == 'chapter_title':
            flush_list(); flush_alert()
            parts.append(f'<h1 class="chapter-title">{esc(t)}</h1>')

        elif role == 'section_header':
            flush_list(); flush_alert()
            parts.append(f'<div class="section-header">{esc(t)}</div>')

        elif role == 'topic_header':
            flush_list(); flush_alert()
            parts.append(f'<div class="topic-header">{esc(t)}</div>')

        elif role == 'subsection':
            flush_list(); flush_alert()
            parts.append(f'<div class="subsection">{esc(t)}</div>')

        elif role == 'warning':
            flush_list(); flush_alert()
            pending = {'type': 'warn', 'title': t, 'items': []}

        elif role == 'hint':
            flush_list(); flush_alert()
            pending = {'type': 'hint', 'title': t, 'items': []}
            flush_alert()   # El hint-box es solo el título callout; el body siguiente fluye normal

        elif role == 'note':
            flush_list(); flush_alert()
            pending = {'type': 'note', 'title': t, 'items': []}

        elif role == 'bullet':
            flush_alert()
            if not in_list:
                parts.append('<ul>')
                in_list = True
            item = BULLET_START.sub('', t).strip()
            # Separar bullets embebidos: "texto • otro • más" → varios <li>
            sub_items = re.split(r'\s*[•►▸■◆]\s+', item)
            for sub in sub_items:
                if sub.strip():
                    parts.append(f'<li>{esc(sub.strip())}</li>')

        elif role == 'figure_caption':
            flush_list(); flush_alert()
            parts.append(f'<p class="figure-caption">{esc(t)}</p>')

        elif role == 'raw_html':
            flush_list(); flush_alert()
            parts.append(b.get('html', ''))

        elif role == 'figure_image':
            flush_list(); flush_alert()
            src = b.get('src', '')
            alt = b.get('alt', '')
            parts.append(
                f'<div class="figure">'
                f'<img src="{esc(src)}" alt="{esc(alt)}">'
                f'</div>'
            )

        elif role == 'cross_ref':
            flush_list(); flush_alert()
            parts.append(f'<p class="cross-ref">{esc(t)}</p>')

        else:  # body
            flush_list(); flush_alert()
            # Si el body tiene bullets embebidos, renderizar como lista
            if re.search(r'[•►▸■◆]\s+', t):
                parts.append('<ul>')
                in_list = True
                for sub in re.split(r'\s*[•►▸■◆]\s+', t):
                    if sub.strip():
                        parts.append(f'<li>{esc(sub.strip())}</li>')
            else:
                parts.append(f'<p>{esc(t)}</p>')

    for b in col_blocks:
        emit(b)
    flush_list()
    flush_alert()
    return parts


# ---------------------------------------------------------------------------
# Recorte de figuras desde el JPEG de página completa
# ---------------------------------------------------------------------------

def crop_figure(page_num: int, fig_id: int,
                crop_pdf: tuple, images_dir: str,
                pdf_w: float = 419.0, pdf_h: float = 595.0) -> str:
    """Recorta una figura del JPEG completo y la guarda. Devuelve ruta relativa o ''."""
    if not HAS_PIL:
        return ''
    src = os.path.join(images_dir, f'page{page_num:03d}_img01.jpeg')
    if not os.path.exists(src):
        return ''
    out_name = f'page{page_num:03d}_fig{fig_id:02d}.jpeg'
    out_path = os.path.join(images_dir, out_name)
    # Siempre regenerar — evita reusar crops de runs anteriores con lógica distinta
    try:
        img = _PILImage.open(src)
        iw, ih = img.size
        sx, sy = iw / pdf_w, ih / pdf_h
        x0, y0, x1, y1 = crop_pdf
        box = (int(x0 * sx), int(y0 * sy), int(x1 * sx), int(y1 * sy))
        cropped = img.crop(box)
        cropped = _trim_whitespace_top(cropped)
        if cropped.size[1] < 20:   # crop vacío tras trim → descartar
            return ''
        cropped.save(out_path, 'JPEG', quality=88)
    except Exception as e:
        print(f"  crop_figure error: {e}")
        return ''
    return f'images/{out_name}'


def _trim_whitespace_top(img, white_threshold: int = 248, sample_step: int = 8,
                          min_nonwhite_fraction: float = 0.01, buffer_px: int = 4) -> '_PILImage.Image':
    """Elimina filas blancas vacías del tope del crop.

    Busca la primera fila donde al menos min_nonwhite_fraction de los píxeles
    muestreados NO son blancos (< white_threshold en algún canal RGB).
    Devuelve la imagen recortada desde esa fila menos buffer_px.
    """
    w, h = img.size
    if h == 0 or w == 0:
        return img
    rgb = img.convert('RGB')
    xs = list(range(0, w, sample_step)) or [w // 2]
    min_nonwhite = max(1, int(len(xs) * min_nonwhite_fraction))
    first_row = 0
    for y in range(h):
        nonwhite = sum(1 for x in xs if any(c < white_threshold for c in rgb.getpixel((x, y))))
        if nonwhite >= min_nonwhite:
            first_row = max(0, y - buffer_px)
            break
    return img.crop((0, first_row, w, h)) if first_row > 0 else img


# ---------------------------------------------------------------------------
# Tabla de luces de advertencia (sub-columnas dentro de la col izquierda)
# ---------------------------------------------------------------------------

# Rangos X dentro de la columna izquierda (en pt sobre página de 419pt)
_TABLE_X_REASON   = 50   # x0 >= 50  → columna "razón"
_TABLE_X_SOLUTION = 135  # x0 >= 135 → columna "solución"
_TABLE_Y_START    = 185  # y mínima de la tabla
_TABLE_Y_END      = 355  # y máxima de la tabla


def _cluster_blocks_by_y(blocks: list, gap: float = 8.0) -> list[list]:
    """Agrupa bloques en filas según proximidad vertical."""
    if not blocks:
        return []
    rows, row = [], [blocks[0]]
    for b in blocks[1:]:
        if b['bbox'][1] - row[-1]['bbox'][3] > gap:
            rows.append(row)
            row = [b]
        else:
            row.append(b)
    rows.append(row)
    return rows


def extract_table_zone(left_raw: list, col_split: float,
                        indicator_raw: list = None) -> tuple:
    """Separa bloques de tabla y no-tabla en la columna izquierda.

    Devuelve (non_table_blocks, table_html_or_None).
    indicator_raw: bloques de indicadores de color (ÿ glifos) recolectados antes de is_skip.
    """
    table_zone, non_table = [], []
    for b in left_raw:
        y0 = b['bbox'][1]
        x0 = b['bbox'][0]
        if _TABLE_Y_START <= y0 <= _TABLE_Y_END and x0 < col_split - 10:
            table_zone.append(b)
        else:
            non_table.append(b)

    if not table_zone:
        return left_raw, None

    # Fila de encabezados (y < TABLE_Y_START + 30)
    h_threshold = _TABLE_Y_START + 30
    header_blocks = [b for b in table_zone if b['bbox'][1] < h_threshold]
    data_blocks   = [b for b in table_zone if b['bbox'][1] >= h_threshold]

    h_reason   = ' '.join(clean(b['text']) for b in header_blocks
                          if _TABLE_X_REASON <= b['bbox'][0] < _TABLE_X_SOLUTION)
    h_solution = ' '.join(clean(b['text']) for b in header_blocks
                          if b['bbox'][0] >= _TABLE_X_SOLUTION)

    # Bloques de razón y solución
    reason_raw   = sorted([b for b in data_blocks
                           if _TABLE_X_REASON <= b['bbox'][0] < _TABLE_X_SOLUTION],
                          key=lambda b: b['bbox'][1])
    solution_raw = sorted([b for b in data_blocks if b['bbox'][0] >= _TABLE_X_SOLUTION],
                          key=lambda b: b['bbox'][1])
    full_raw     = sorted([b for b in data_blocks if b['bbox'][0] < _TABLE_X_REASON],
                          key=lambda b: b['bbox'][1])

    # Solo es tabla real si hay datos en AMBAS columnas (razón Y solución)
    if not solution_raw or not reason_raw:
        return left_raw, None

    def merge_rows(blocks):
        rows_of_blocks = _cluster_blocks_by_y(blocks, gap=6.0)
        return [' '.join(clean(b['text']) for b in row) for row in rows_of_blocks]

    def dedup_cell(text):
        """Elimina frases repetidas: 'Es normal. Es normal.' → 'Es normal.'"""
        sentences = [s.strip() for s in re.split(r'(?<=\.)\s+', text) if s.strip()]
        seen, unique = [], []
        for s in sentences:
            if s not in seen:
                seen.append(s)
                unique.append(s)
        return ' '.join(unique)

    reason_rows   = merge_rows(reason_raw)
    solution_rows = [dedup_cell(s) for s in merge_rows(solution_raw)]
    full_rows     = [clean(b['text']) for b in full_raw]

    # Construir filas de indicadores de color (ÿ glifos con color)
    indicator_rows = []
    if indicator_raw:
        ind_sorted = sorted(indicator_raw, key=lambda b: b['bbox'][1])
        ind_row_groups = _cluster_blocks_by_y(ind_sorted, gap=15.0)
        for row_blocks in ind_row_groups:
            dots = []
            for b in row_blocks:
                c = b.get('color', '')
                if c in ('#ee1d23', '#ee1c24'):
                    dots.append('<span style="color:#ee1d23;font-size:11pt">ÿ</span>')
                elif c == '#71bf44':
                    dots.append('<span style="color:#71bf44;font-size:11pt">ÿ</span>')
                else:
                    dots.append('<span style="color:#888888;font-size:11pt">ÿ</span>')
            indicator_rows.append('&nbsp;'.join(dots))

    # Fusionar filas huérfanas (sin indicador ni razón) con la fila anterior en solución
    # Caso: "Es normal. Es" + fila siguiente vacía "normal." → "Es normal."
    if indicator_rows:
        merged_ind, merged_rea, merged_sol = [], [], []
        n_raw = max(len(indicator_rows), len(reason_rows), len(solution_rows))
        for i in range(n_raw):
            ind = indicator_rows[i] if i < len(indicator_rows) else ''
            r   = reason_rows[i]   if i < len(reason_rows)    else ''
            s   = solution_rows[i] if i < len(solution_rows)  else ''
            if not ind and not r and merged_sol:
                merged_sol[-1] = dedup_cell(merged_sol[-1] + ' ' + s)
            else:
                merged_ind.append(ind)
                merged_rea.append(r)
                merged_sol.append(s)
        indicator_rows = merged_ind
        reason_rows    = merged_rea
        solution_rows  = merged_sol

    # Construir HTML
    has_indicators = bool(indicator_rows)
    if has_indicators:
        parts = ['<table class="warn-table">',
                 '<thead><tr>',
                 '<th style="width:32pt;text-align:center">Luz</th>',
                 f'<th>{esc(h_reason or "Posible razón")}</th>',
                 f'<th>{esc(h_solution or "Solución")}</th>',
                 '</tr></thead><tbody>']
        n = max(len(indicator_rows), len(reason_rows), len(solution_rows))
        for i in range(n):
            ind = indicator_rows[i] if i < len(indicator_rows) else ''
            r   = reason_rows[i]   if i < len(reason_rows)    else ''
            s   = solution_rows[i] if i < len(solution_rows)  else ''
            parts.append(
                f'<tr>'
                f'<td style="text-align:center;vertical-align:middle">{ind}</td>'
                f'<td>{esc(r)}</td>'
                f'<td>{esc(s)}</td>'
                f'</tr>'
            )
    else:
        parts = ['<table class="warn-table">',
                 '<thead><tr>',
                 f'<th>{esc(h_reason or "Posible razón")}</th>',
                 f'<th>{esc(h_solution or "Solución")}</th>',
                 '</tr></thead><tbody>']
        n = max(len(reason_rows), len(solution_rows))
        for i in range(n):
            r = reason_rows[i]   if i < len(reason_rows)   else ''
            s = solution_rows[i] if i < len(solution_rows) else ''
            parts.append(f'<tr><td>{esc(r)}</td><td>{esc(s)}</td></tr>')

    for fr in full_rows:
        colspan = '3' if has_indicators else '2'
        parts.append(f'<tr><td colspan="{colspan}">{esc(fr)}</td></tr>')

    parts.append('</tbody></table>')
    return non_table, '\n'.join(parts)


# ---------------------------------------------------------------------------
# Constructor HTML para una página
# ---------------------------------------------------------------------------

def _inject_figures(col_raw: list, page_num: int,
                    col_x0: float, col_x1: float,
                    images_dir: str, fig_id_start: int) -> tuple:
    """Inserta pseudo-bloques de imagen antes de cada caption de figura.

    Devuelve (nuevo_col_raw, next_fig_id).
    prev_img_y_bottom se actualiza con TODOS los bloques (no solo captions)
    para que el crop empiece justo después del último contenido visible,
    evitando incluir cabeceras de sección y cajas ADVERTENCIA del JPEG.
    """
    result = []
    fig_id = fig_id_start
    prev_img_y_bottom = 55.0  # fallback: debajo del header de página

    for b in col_raw:
        t = clean(b.get('text', ''))
        if FIG_RE.match(t):
            # Cross-ref multi-figura: "Figura 27 Figura 28..." — no es caption real
            if re.match(r'^Figura\s+\d+\s+(Figura|Fig\.)', t, re.I):
                prev_img_y_bottom = max(prev_img_y_bottom, b['bbox'][3] + 2.0)
                result.append(b)
                continue

            cap_y_top = b['bbox'][1]
            # Solo insertar imagen si el área disponible tiene al menos 40pt de altura
            if (cap_y_top - prev_img_y_bottom) >= 40.0:
                crop_box = (col_x0, prev_img_y_bottom, col_x1, cap_y_top)
                rel = crop_figure(page_num, fig_id, crop_box, images_dir)
                if rel:
                    result.append({
                        'type': 'figure_image',
                        'bbox': list(crop_box),
                        'src':  rel,
                        'alt':  t,
                        'text': '',
                        'size': 0,
                        'color': '#000000',
                    })
                    fig_id += 1
            prev_img_y_bottom = b['bbox'][3] + 2.0
        else:
            # Actualizar posición con bloques no-figura: la imagen empieza
            # DESPUÉS del último bloque de texto/contenido visible en la columna
            prev_img_y_bottom = max(prev_img_y_bottom, b['bbox'][3] + 2.0)
        result.append(b)
    return result, fig_id


def page_to_html(page_data: dict, page_num: int, images_dir: str) -> str:
    blocks    = page_data.get('blocks', [])
    pw        = page_data.get('width',  419.0)
    ph        = page_data.get('height', 595.0)
    col_split = pw * 0.48   # ≈ 201pt

    # ── 1. Filtrar y separar en columnas ──
    # Antes del filtro, recolectar bloques de indicadores de color para la tabla
    # (bloques ÿ en zona x<50, y=185-355 con colores específicos — filtrados por is_skip
    # porque clean('ÿ')='' pero necesitamos su color para la primera columna de la tabla)
    table_indicator_raw = [
        b for b in blocks
        if b.get('type') != 'image'
        and _TABLE_Y_START <= b['bbox'][1] <= _TABLE_Y_END
        and b['bbox'][0] < _TABLE_X_REASON
        and not clean(b.get('text', ''))   # solo glifos ÿ (quedan vacíos tras clean)
        and b.get('color', '') in ('#ee1d23', '#71bf44', '#231f20', '#ee1c24')
        and b.get('size', 0) >= 5.0        # descartar fragmentos de ruido
    ]

    left_raw, right_raw = [], []
    for b in blocks:
        if b.get('type') == 'image':
            continue
        if not is_skip(b):
            cx = (b['bbox'][0] + b['bbox'][2]) / 2
            (left_raw if cx < col_split else right_raw).append(b)

    left_raw.sort( key=lambda b: b['bbox'][1])
    right_raw.sort(key=lambda b: b['bbox'][1])

    # ── 2. Extraer tabla de la columna izquierda ──
    left_raw, table_html = extract_table_zone(left_raw, col_split,
                                              indicator_raw=table_indicator_raw)

    # ── 3. Inyectar imágenes recortadas antes de cada caption de figura ──
    left_raw,  next_id = _inject_figures(left_raw,  page_num, 0,         col_split, images_dir, 1)
    right_raw, _       = _inject_figures(right_raw, page_num, col_split,  pw,        images_dir, next_id)

    # ── 4. Mergear fragmentos en unidades semánticas ──
    left_blocks  = merge_column_blocks(left_raw)
    right_blocks = merge_column_blocks(right_raw)

    # ── 5. Insertar tabla en posición correcta dentro de left_blocks ──
    # La tabla va justo después del último figure_caption de la columna izquierda
    # (o al inicio si no hay captions)
    if table_html:
        table_block = {
            'type':  'raw_html',
            'html':  table_html,
            'text':  '',
            'size':  0,
            'color': '#000000',
            'bbox':  [0, _TABLE_Y_START, col_split, _TABLE_Y_END],
        }
        # Insertar después del último figure_caption
        insert_pos = 0
        for i, b in enumerate(left_blocks):
            if classify(b) == 'figure_caption':
                insert_pos = i + 1
        left_blocks.insert(insert_pos, table_block)

    page_parts = [f'<p class="page-sep">pág. {page_num}</p>']

    # ── 6. Renderizar en una sola columna (col izquierda primero, luego derecha)
    all_blocks = left_blocks + right_blocks
    page_parts.extend(render_blocks(all_blocks))

    return '\n'.join(page_parts)


# ---------------------------------------------------------------------------
# Parseo de rango de páginas
# ---------------------------------------------------------------------------

def parse_pages(spec: str) -> list:
    pages = []
    for part in spec.split(','):
        part = part.strip()
        if '-' in part:
            a, b = part.split('-', 1)
            pages.extend(range(int(a), int(b) + 1))
        else:
            pages.append(int(part))
    return sorted(set(pages))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def rebuild_html(proofread_path: str, job_dir: str,
                 page_spec: str = '29-31',
                 output_pdf: str = None) -> str:

    images_dir = os.path.join(job_dir, 'images')
    if output_pdf is None:
        output_pdf = os.path.join(job_dir, 'output_cliente.pdf')

    with open(proofread_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    pages = parse_pages(page_spec)
    total = len(data['pages'])
    print(f"  Pages to render: {pages}")

    TOPIC_STARTS = {29, 70, 134}

    body_parts = []
    for pg_num in pages:
        if pg_num < 1 or pg_num > total:
            continue
        page_data = data['pages'][pg_num - 1]
        html = page_to_html(page_data, pg_num, images_dir)
        if pg_num in TOPIC_STARTS and body_parts:
            body_parts.append('<div class="topic-break"></div>')
        body_parts.append(html)

    full_html = HTML_DOC.format(css=CSS, body='\n'.join(body_parts))

    html_out = output_pdf.replace('.pdf', '.html')
    with open(html_out, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print(f"  HTML → {html_out}")

    try:
        from weasyprint import HTML as WP
        print("  Converting with weasyprint...")
        WP(string=full_html, base_url=job_dir).write_pdf(output_pdf)
        size_mb = os.path.getsize(output_pdf) / 1024 / 1024
        print(f"  PDF → {output_pdf}  ({size_mb:.1f} MB)")
    except Exception as e:
        print(f"  weasyprint failed: {e}")
        print(f"  HTML: {html_out}")

    return output_pdf


if __name__ == '__main__':
    args  = sys.argv[1:]
    pjson = args[0] if len(args) > 0 else 'jobs/test-001/proofread.json'
    jdir  = args[1] if len(args) > 1 else 'jobs/test-001'
    pspec = '29-31'   # default: primeras 3 páginas

    for idx, a in enumerate(args):
        if a == '--pages' and idx + 1 < len(args):
            pspec = args[idx + 1]
        elif a.startswith('--pages='):
            pspec = a.split('=', 1)[1]

    rebuild_html(pjson, jdir, pspec)
