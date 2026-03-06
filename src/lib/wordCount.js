import * as pdfjsLib from "pdfjs-dist";
import mammoth from "mammoth";

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url
).toString();

function countWordsInText(text) {
  return text
    .split(/\s+/)
    .filter((w) => w.length > 0).length;
}

/**
 * Parse page ranges like "3-7, 48-56, 68-93" into a Set of page numbers.
 * Returns null if empty (means all pages).
 */
function parsePageRanges(pagesStr) {
  if (!pagesStr || !pagesStr.trim()) return null;
  const pages = new Set();
  for (const part of pagesStr.split(",")) {
    const trimmed = part.trim();
    const match = trimmed.match(/^(\d+)\s*-\s*(\d+)$/);
    if (match) {
      const start = parseInt(match[1], 10);
      const end = parseInt(match[2], 10);
      for (let i = start; i <= end; i++) pages.add(i);
    } else if (/^\d+$/.test(trimmed)) {
      pages.add(parseInt(trimmed, 10));
    }
  }
  return pages.size > 0 ? pages : null;
}

async function countWordsInPdf(file, pageSet) {
  const buf = await file.arrayBuffer();
  const pdf = await pdfjsLib.getDocument({ data: buf }).promise;
  let totalWords = 0;

  for (let i = 1; i <= pdf.numPages; i++) {
    if (pageSet && !pageSet.has(i)) continue;
    const page = await pdf.getPage(i);
    const content = await page.getTextContent();
    const text = content.items.map((item) => item.str).join(" ");
    totalWords += countWordsInText(text);
  }

  return totalWords;
}

async function countWordsInDocx(file) {
  const buf = await file.arrayBuffer();
  const result = await mammoth.extractRawText({ arrayBuffer: buf });
  return countWordsInText(result.value);
}

/**
 * Count words in a file. Returns { words, method } or null if unsupported.
 * method: 'exact' for PDF/DOCX, 'estimate' for fallback.
 */
export async function countWords(file, pagesStr = "") {
  try {
    const pageSet = parsePageRanges(pagesStr);

    if (file.type === "application/pdf" || file.name?.endsWith(".pdf")) {
      const words = await countWordsInPdf(file, pageSet);
      return { words, method: "exact" };
    }

    const docxTypes = [
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "application/msword",
    ];
    if (docxTypes.includes(file.type) || /\.docx?$/.test(file.name)) {
      const words = await countWordsInDocx(file);
      return { words, method: "exact" };
    }

    if (file.type?.startsWith("text/")) {
      const text = await file.text();
      return { words: countWordsInText(text), method: "exact" };
    }

    // Images and other formats: can't count words client-side
    if (file.type?.startsWith("image/")) {
      return null;
    }

    // Rough estimate fallback
    const estimatedWords = Math.max(1, Math.ceil(file.size / 6));
    return { words: estimatedWords, method: "estimate" };
  } catch (err) {
    console.error("Word count error:", err);
    return null;
  }
}
