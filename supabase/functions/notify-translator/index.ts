import { serve } from "https://deno.land/std@0.177.0/http/server.ts";

const RESEND_API_KEY = Deno.env.get("RESEND_API_KEY") ?? "";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface NotifyRequest {
  translator_email: string;
  translator_name: string;
  job_id: string;
  job_title: string;
  doc_type: string;
  pages: number;
  review_score: number;
  issues_summary: { total: number; critical: number; major: number; minor: number };
  download_urls: { [key: string]: string };
}

function buildEmailHtml(data: NotifyRequest): string {
  const scorePercent = Math.round(data.review_score * 100);
  const scoreColor = scorePercent >= 95 ? "#22c55e" : scorePercent >= 80 ? "#eab308" : "#ef4444";

  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <div style="max-width:600px;margin:0 auto;background:#ffffff;">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#1e293b 0%,#334155 100%);padding:32px 40px;text-align:center;">
      <h1 style="color:#ffffff;font-size:28px;margin:0;letter-spacing:1px;">HUMARA</h1>
      <p style="color:#94a3b8;font-size:13px;margin:8px 0 0;">Traducciones certificadas con IA</p>
    </div>

    <!-- Body -->
    <div style="padding:32px 40px;">
      <p style="font-size:16px;color:#1e293b;margin:0 0 24px;">
        Hola <strong>${data.translator_name}</strong>,
      </p>
      <p style="font-size:15px;color:#475569;line-height:1.6;margin:0 0 24px;">
        Tenés una nueva traducción lista para revisión y certificación.
      </p>

      <!-- Job Card -->
      <div style="background:#f1f5f9;border-radius:12px;padding:24px;margin:0 0 24px;">
        <h2 style="font-size:18px;color:#1e293b;margin:0 0 16px;">${data.job_title}</h2>
        <table style="width:100%;border-collapse:collapse;">
          <tr>
            <td style="padding:6px 0;color:#64748b;font-size:13px;">Tipo de documento</td>
            <td style="padding:6px 0;color:#1e293b;font-size:13px;text-align:right;font-weight:600;">${data.doc_type}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#64748b;font-size:13px;">Páginas</td>
            <td style="padding:6px 0;color:#1e293b;font-size:13px;text-align:right;font-weight:600;">${data.pages}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#64748b;font-size:13px;">Idioma</td>
            <td style="padding:6px 0;color:#1e293b;font-size:13px;text-align:right;font-weight:600;">Inglés → Español</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#64748b;font-size:13px;">Score de revisión IA</td>
            <td style="padding:6px 0;font-size:13px;text-align:right;">
              <span style="background:${scoreColor};color:#fff;padding:2px 10px;border-radius:12px;font-weight:600;">${scorePercent}%</span>
            </td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#64748b;font-size:13px;">Observaciones</td>
            <td style="padding:6px 0;color:#1e293b;font-size:13px;text-align:right;">
              ${data.issues_summary.critical} críticas · ${data.issues_summary.major} mayores · ${data.issues_summary.minor} menores
            </td>
          </tr>
        </table>
      </div>

      <!-- Download Buttons -->
      <div style="text-align:center;margin:0 0 12px;">
        <a href="${data.download_urls["original.pdf"] || "#"}"
           style="display:inline-block;background:#1e293b;color:#ffffff;text-decoration:none;padding:14px 32px;border-radius:8px;font-size:14px;font-weight:600;margin:6px;">
          📄 Descargar Original (PDF)
        </a>
      </div>
      <div style="text-align:center;margin:0 0 24px;">
        <a href="${data.download_urls["traduccion.docx"] || "#"}"
           style="display:inline-block;background:#2563eb;color:#ffffff;text-decoration:none;padding:14px 32px;border-radius:8px;font-size:14px;font-weight:600;margin:6px;">
          📝 Descargar Traducción (Word)
        </a>
      </div>

      <!-- Instructions -->
      <div style="background:#eff6ff;border-left:4px solid #2563eb;padding:16px 20px;border-radius:0 8px 8px 0;margin:0 0 24px;">
        <p style="font-size:13px;color:#1e40af;margin:0 0 8px;font-weight:600;">Instrucciones</p>
        <ol style="font-size:13px;color:#1e3a5f;margin:0;padding-left:20px;line-height:1.8;">
          <li>Descargá el <strong>Word</strong> — contiene la traducción completa con comentarios de revisión en rojo</li>
          <li>Revisá especialmente los segmentos marcados con <strong>[REVISIÓN]</strong></li>
          <li>Editá lo que consideres necesario — el documento es 100% editable</li>
          <li>La fórmula de certificación está al final, lista para tu firma</li>
        </ol>
      </div>

      <p style="font-size:13px;color:#94a3b8;text-align:center;margin:24px 0 0;">
        Los links de descarga vencen en 7 días.
      </p>
    </div>

    <!-- Footer -->
    <div style="background:#f8fafc;padding:24px 40px;text-align:center;border-top:1px solid #e2e8f0;">
      <p style="font-size:12px;color:#94a3b8;margin:0;">
        Humara · Traducciones certificadas · humara.app
      </p>
    </div>
  </div>
</body>
</html>`;
}

serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const data: NotifyRequest = await req.json();

    if (!data.translator_email || !data.job_id) {
      return new Response(
        JSON.stringify({ error: "translator_email and job_id required" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const html = buildEmailHtml(data);

    // Send via Resend API
    const resendResponse = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${RESEND_API_KEY}`,
      },
      body: JSON.stringify({
        from: "Humara <onboarding@resend.dev>",
        to: [data.translator_email],
        subject: `Nueva traducción para revisar: ${data.job_title}`,
        html: html,
      }),
    });

    const resendData = await resendResponse.json();

    if (!resendResponse.ok) {
      return new Response(
        JSON.stringify({ error: "Failed to send email", details: resendData }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    return new Response(
      JSON.stringify({ success: true, email_id: resendData.id }),
      { status: 200, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (err) {
    return new Response(
      JSON.stringify({ error: err.message }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
