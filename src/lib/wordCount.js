import * as pdfjsLib from "pdfjs-dist";
import mammoth from "mammoth";
import { supabase } from "./supabase";

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url
).toString();

function countWordsInText(text) {
  return text
    .split(/\s+/)
    .filter((w) => w.length > 0).length;
}

// Common words for simple language detection
const ES_WORDS = new Set(["de","la","el","en","y","los","del","las","un","por","con","una","su","para","es","al","lo","como","más","pero","sus","le","ya","fue","este","ha","desde","son","entre","está","cuando","muy","sin","sobre","ser","también","me","hasta","hay","donde","han","sido","tiene","año","se","nos","ni","todo","esta","era","parte","después","años","dos","cada","ese","hoy","durante","otro"]);
const EN_WORDS = new Set(["the","of","and","to","in","a","is","that","for","it","as","was","with","be","by","on","not","he","this","are","or","his","from","at","which","but","have","an","had","they","you","were","their","been","has","its","who","did","will","each","about","how","up","out","them","then","she","many","some","so","these","would","other","into","more","her","two","like","him","see","time","could","no","make","than","first","now","way","may","down","over","new","after"]);

/**
 * Detect language from text using word frequency heuristic.
 * Returns "en", "es", or null if uncertain.
 */
function detectLanguage(text) {
  const words = text.toLowerCase().split(/\s+/).filter((w) => w.length > 1);
  const sample = words.slice(0, 300);
  if (sample.length < 20) return null;

  let enCount = 0;
  let esCount = 0;
  for (const w of sample) {
    if (EN_WORDS.has(w)) enCount++;
    if (ES_WORDS.has(w)) esCount++;
  }

  if (enCount > esCount * 1.5) return "en";
  if (esCount > enCount * 1.5) return "es";
  return enCount > esCount ? "en" : esCount > enCount ? "es" : null;
}

/**
 * Count words using server-side OCR (Claude Vision) for scanned PDFs and images.
 * Returns full analysis: words, pages, language, doc_type, notes.
 */
async function countWordsWithOCR(file, pagesStr = "") {
  try {
    const formData = new FormData();
    formData.append("file", file);
    if (pagesStr) formData.append("pages", pagesStr);

    const { data, error } = await supabase.functions.invoke("count-words", {
      body: formData,
    });

    if (error || !data?.words) return null;
    return {
      words: data.words,
      pages: data.pages || null,
      language: data.language || null,
      docType: data.doc_type || null,
      notes: data.notes || null,
      method: "ocr",
    };
  } catch {
    return null;
  }
}

/**
 * Parse page ranges like "3-7, 48-56, 68-93" into a Set of page numbers.
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
  let allText = "";

  for (let i = 1; i <= pdf.numPages; i++) {
    if (pageSet && !pageSet.has(i)) continue;
    const page = await pdf.getPage(i);
    const content = await page.getTextContent();
    const text = content.items.map((item) => item.str).join(" ");
    totalWords += countWordsInText(text);
    if (allText.length < 2000) allText += " " + text;
  }

  return { words: totalWords, text: allText, pages: pdf.numPages };
}

async function countWordsInDocx(file) {
  const buf = await file.arrayBuffer();
  const result = await mammoth.extractRawText({ arrayBuffer: buf });
  return { words: countWordsInText(result.value), text: result.value };
}

/**
 * Count words in a file. Returns analysis object or null if unsupported.
 * { words, method, language?, pages?, docType?, notes? }
 */
export async function countWords(file, pagesStr = "") {
  try {
    const pageSet = parsePageRanges(pagesStr);

    if (file.type === "application/pdf" || file.name?.endsWith(".pdf")) {
      const result = await countWordsInPdf(file, pageSet);
      if (result.words > 0) {
        const language = detectLanguage(result.text);
        return {
          words: result.words,
          pages: result.pages,
          language,
          method: "exact",
        };
      }
      // Scanned PDF — use server OCR (gets language from Claude)
      const ocrResult = await countWordsWithOCR(file, pagesStr);
      if (ocrResult) return ocrResult;
      return null;
    }

    const docxTypes = [
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "application/msword",
    ];
    if (docxTypes.includes(file.type) || /\.docx?$/.test(file.name)) {
      const result = await countWordsInDocx(file);
      const language = detectLanguage(result.text);
      return { words: result.words, language, method: "exact" };
    }

    if (file.type?.startsWith("text/")) {
      const text = await file.text();
      const language = detectLanguage(text);
      return { words: countWordsInText(text), language, method: "exact" };
    }

    // Images — use server OCR
    if (file.type?.startsWith("image/")) {
      const ocrResult = await countWordsWithOCR(file, pagesStr);
      if (ocrResult) return ocrResult;
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
