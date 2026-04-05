"""Step 6: Notify translator via email when translation is ready.

Sends an HTML email directly via Resend API with download links.

Usage:
    python notify.py <job_id> --email andrea@example.com --name Andrea
"""

import json
import os
import sys

import requests

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")


def build_email_html(data):
    """Build the HTML email template."""
    score_percent = round(data["review_score"] * 100)
    if score_percent >= 95:
        score_color = "#22c55e"
    elif score_percent >= 80:
        score_color = "#eab308"
    else:
        score_color = "#ef4444"

    iss = data["issues_summary"]

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
<div style="max-width:600px;margin:0 auto;background:#ffffff;">

  <div style="background:linear-gradient(135deg,#1e293b 0%,#334155 100%);padding:32px 40px;text-align:center;">
    <h1 style="color:#ffffff;font-size:28px;margin:0;letter-spacing:1px;">HUMARA</h1>
    <p style="color:#94a3b8;font-size:13px;margin:8px 0 0;">Traducciones certificadas con IA</p>
  </div>

  <div style="padding:32px 40px;">
    <p style="font-size:16px;color:#1e293b;margin:0 0 24px;">
      Hola <strong>{data["translator_name"]}</strong>,
    </p>
    <p style="font-size:15px;color:#475569;line-height:1.6;margin:0 0 24px;">
      Tenés una nueva traducción lista para revisión y certificación.
    </p>

    <div style="background:#f1f5f9;border-radius:12px;padding:24px;margin:0 0 24px;">
      <h2 style="font-size:18px;color:#1e293b;margin:0 0 16px;">{data["job_title"]}</h2>
      <table style="width:100%;border-collapse:collapse;">
        <tr>
          <td style="padding:6px 0;color:#64748b;font-size:13px;">Tipo de documento</td>
          <td style="padding:6px 0;color:#1e293b;font-size:13px;text-align:right;font-weight:600;">{data["doc_type"]}</td>
        </tr>
        <tr>
          <td style="padding:6px 0;color:#64748b;font-size:13px;">Páginas</td>
          <td style="padding:6px 0;color:#1e293b;font-size:13px;text-align:right;font-weight:600;">{data["pages"]}</td>
        </tr>
        <tr>
          <td style="padding:6px 0;color:#64748b;font-size:13px;">Idioma</td>
          <td style="padding:6px 0;color:#1e293b;font-size:13px;text-align:right;font-weight:600;">Inglés → Español</td>
        </tr>
        <tr>
          <td style="padding:6px 0;color:#64748b;font-size:13px;">Score de revisión IA</td>
          <td style="padding:6px 0;font-size:13px;text-align:right;">
            <span style="background:{score_color};color:#fff;padding:2px 10px;border-radius:12px;font-weight:600;">{score_percent}%</span>
          </td>
        </tr>
        <tr>
          <td style="padding:6px 0;color:#64748b;font-size:13px;">Observaciones</td>
          <td style="padding:6px 0;color:#1e293b;font-size:13px;text-align:right;">
            {iss["critical"]} críticas · {iss["major"]} mayores · {iss["minor"]} menores
          </td>
        </tr>
      </table>
    </div>

    <div style="text-align:center;margin:0 0 12px;">
      <a href="{data["download_urls"].get("traduccion.docx", "#")}"
         style="display:inline-block;background:#2563eb;color:#ffffff;text-decoration:none;padding:14px 32px;border-radius:8px;font-size:14px;font-weight:600;">
        Descargar Traducción (Word)
      </a>
    </div>
    <div style="text-align:center;margin:0 0 24px;">
      <a href="{data["download_urls"].get("original.pdf", "#")}"
         style="display:inline-block;background:#e2e8f0;color:#475569;text-decoration:none;padding:12px 28px;border-radius:8px;font-size:13px;font-weight:600;">
        Ver Original (PDF)
      </a>
    </div>

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

  <div style="background:#f8fafc;padding:24px 40px;text-align:center;border-top:1px solid #e2e8f0;">
    <p style="font-size:12px;color:#94a3b8;margin:0;">
      Humara · Traducciones certificadas · humara.app
    </p>
  </div>
</div>
</body>
</html>"""


def notify_translator(job_id, job_dir, translator_emails, translator_name="Traductor/a"):
    """Send notification email to the translator (and CC recipients).

    Args:
        job_id: Job identifier
        job_dir: Local job directory
        translator_emails: Comma-separated email addresses (first = main, rest = CC)
        translator_name: Name of the main translator

    Returns:
        dict with email_id if successful, None otherwise
    """
    if not RESEND_API_KEY:
        print("  Error: RESEND_API_KEY not set")
        return None

    # Load download URLs
    urls_path = os.path.join(job_dir, "download_urls.json")
    if not os.path.exists(urls_path):
        print(f"  Error: {urls_path} not found — run upload step first")
        return None

    with open(urls_path, "r") as f:
        download_urls = json.load(f)

    # Load review report
    report_path = os.path.join(job_dir, "review_report.json")
    review_score = 0.0
    issues_summary = {"total": 0, "critical": 0, "major": 0, "minor": 0}
    if os.path.exists(report_path):
        with open(report_path, "r") as f:
            report = json.load(f)
        review_score = report.get("score", 0.0)
        issues_summary = report.get("issues_summary", issues_summary)

    # Load metadata
    reviewed_path = os.path.join(job_dir, "reviewed.json")
    pages = 0
    doc_type = "general"
    if os.path.exists(reviewed_path):
        with open(reviewed_path, "r") as f:
            reviewed = json.load(f)
        meta = reviewed.get("metadata", {})
        pages = meta.get("pages", 0)
        doc_type = meta.get("doc_type", "general")

    # Build job title
    job_title = job_id.replace("-", " ").replace("_", " ").title()

    data = {
        "translator_name": translator_name,
        "job_title": job_title,
        "doc_type": doc_type.capitalize(),
        "pages": pages,
        "review_score": review_score,
        "issues_summary": issues_summary,
        "download_urls": download_urls,
    }

    html = build_email_html(data)

    # Parse emails: first = to, rest = cc
    emails = [e.strip() for e in translator_emails.split(",")]
    to_email = emails[0]
    cc_emails = emails[1:] if len(emails) > 1 else []

    # Determine sender domain
    # Use humara.app if verified, fallback to onboarding@resend.dev
    from_email = "Humara <traducciones@humara.app>"

    email_payload = {
        "from": from_email,
        "to": [to_email],
        "subject": f"Nueva traducción para revisar: {job_title}",
        "html": html,
    }
    if cc_emails:
        email_payload["cc"] = cc_emails

    print(f"  To: {to_email}")
    if cc_emails:
        print(f"  CC: {', '.join(cc_emails)}")

    try:
        r = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json=email_payload,
            timeout=15,
        )

        if r.status_code == 200:
            result = r.json()
            print(f"  ✓ Email sent (id: {result.get('id', 'n/a')})")
            return result
        else:
            print(f"  ✗ Failed: {r.status_code} {r.text}")
            # Retry with fallback sender
            if "humara.app" in from_email:
                print("  Retrying with fallback sender...")
                email_payload["from"] = "Humara <onboarding@resend.dev>"
                r2 = requests.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {RESEND_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json=email_payload,
                    timeout=15,
                )
                if r2.status_code == 200:
                    result = r2.json()
                    print(f"  ✓ Email sent with fallback sender (id: {result.get('id', 'n/a')})")
                    return result
                else:
                    print(f"  ✗ Fallback also failed: {r2.status_code} {r2.text}")
            return None

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Notify translator via email")
    parser.add_argument("job_id", help="Job ID")
    parser.add_argument("--email", required=True,
                        help="Email addresses, comma-separated (first=to, rest=cc)")
    parser.add_argument("--name", default="Traductor/a", help="Translator name")
    args = parser.parse_args()

    job_dir = os.path.join(os.path.dirname(__file__), "jobs", args.job_id)
    notify_translator(args.job_id, job_dir, args.email, args.name)
