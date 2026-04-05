import { serve } from "https://deno.land/std@0.177.0/http/server.ts";

const ANTHROPIC_API_KEY = Deno.env.get("ANTHROPIC_API_KEY")!;

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers":
    "Content-Type, Authorization, apikey, x-client-info",
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: CORS_HEADERS });
  }

  try {
    const formData = await req.formData();
    const file = formData.get("file") as File | null;
    const pagesStr = formData.get("pages") as string | null;

    if (!file) {
      return new Response(JSON.stringify({ error: "file required" }), {
        status: 400,
        headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
      });
    }

    // Convert file to base64
    const arrayBuffer = await file.arrayBuffer();
    const base64 = btoa(
      new Uint8Array(arrayBuffer).reduce(
        (data, byte) => data + String.fromCharCode(byte),
        ""
      )
    );

    // Determine media type and content block type
    const isImage = file.type?.startsWith("image/");
    const mediaType = isImage ? file.type : "application/pdf";

    // Build the prompt — ask Claude to count words precisely
    const pageInstruction = pagesStr
      ? `Only count words on pages: ${pagesStr}. Ignore all other pages.`
      : "Count words on ALL pages.";

    // Use "image" block for images, "document" block for PDFs
    const fileBlock = isImage
      ? {
          type: "image" as const,
          source: { type: "base64" as const, media_type: mediaType, data: base64 },
        }
      : {
          type: "document" as const,
          source: { type: "base64" as const, media_type: mediaType, data: base64 },
        };

    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: "claude-sonnet-4-20250514",
        max_tokens: 256,
        messages: [
          {
            role: "user",
            content: [
              fileBlock,
              {
                type: "text",
                text: `You are a document analyzer for a certified translation service. ${pageInstruction}

Count EVERY word in the document carefully. Include:
- All body text, headers, footers, captions
- Text in tables, forms, and sidebars
- Legal text, fine print, disclaimers
- Do NOT count page numbers, dates alone, or purely numeric values

Also detect the PRIMARY language of the document and classify its type.

Respond with ONLY a JSON object:
{"words": <number>, "pages": <number>, "language": "<ISO 639-1 code: en, es, pt, fr, etc>", "doc_type": "<legal|commercial|technical|civil|medical|general>", "notes": "<brief description of the document>"}

Be precise — this count determines the client's price quote.`,
              },
            ],
          },
        ],
      }),
    });

    if (!response.ok) {
      const errText = await response.text();
      console.error("Anthropic API error:", response.status, errText);
      return new Response(
        JSON.stringify({ error: "OCR service error", detail: errText }),
        {
          status: 502,
          headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
        }
      );
    }

    const result = await response.json();
    const text = result.content?.[0]?.text || "";

    // Parse the JSON response from Claude
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      return new Response(
        JSON.stringify({ error: "Could not parse word count", raw: text }),
        {
          status: 500,
          headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
        }
      );
    }

    const parsed = JSON.parse(jsonMatch[0]);

    return new Response(
      JSON.stringify({
        words: parsed.words,
        pages: parsed.pages,
        language: parsed.language || null,
        doc_type: parsed.doc_type || null,
        notes: parsed.notes,
        method: "ocr",
      }),
      {
        headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
      }
    );
  } catch (err) {
    console.error("count-words error:", err);
    return new Response(JSON.stringify({ error: "Internal error" }), {
      status: 500,
      headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });
  }
});
