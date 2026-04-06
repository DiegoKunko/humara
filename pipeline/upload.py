"""Step 5: Upload job results to Supabase Storage.

Uploads original PDF, translated DOCX, and review report to Supabase Storage,
then generates signed download URLs (valid 7 days).

Usage:
    python upload.py <job_id>
"""

import json
import os
import sys

import requests


SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://uvhlverpjakhpwihhgef.supabase.co")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
BUCKET = "translations"
SIGNED_URL_EXPIRY = 315360000  # 10 years (en la práctica, no vence)


def get_headers(content_type="application/json"):
    return {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": content_type,
    }


def ensure_bucket():
    """Create the translations bucket if it doesn't exist."""
    r = requests.post(
        f"{SUPABASE_URL}/storage/v1/bucket",
        headers=get_headers(),
        json={
            "id": BUCKET,
            "name": BUCKET,
            "public": False,
            "file_size_limit": 52428800,
            "allowed_mime_types": [
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/json",
            ],
        },
    )
    if r.status_code == 200:
        print(f"  Bucket '{BUCKET}' created")
    elif r.status_code == 409:
        pass  # Already exists
    else:
        print(f"  Warning: bucket creation returned {r.status_code}: {r.text}")


def upload_file(job_id, local_path, remote_name, content_type):
    """Upload a file to Supabase Storage."""
    if not os.path.exists(local_path):
        print(f"  Skip {remote_name} (not found)")
        return False

    with open(local_path, "rb") as f:
        r = requests.post(
            f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{job_id}/{remote_name}",
            headers=get_headers(content_type),
            data=f,
        )

    if r.status_code == 200:
        size_mb = os.path.getsize(local_path) / (1024 * 1024)
        print(f"  ✓ {remote_name} ({size_mb:.1f} MB)")
        return True
    else:
        print(f"  ✗ {remote_name}: {r.status_code} {r.text}")
        return False


def generate_signed_url(job_id, filename):
    """Generate a signed URL for a file (valid 7 days)."""
    r = requests.post(
        f"{SUPABASE_URL}/storage/v1/object/sign/{BUCKET}/{job_id}/{filename}",
        headers=get_headers(),
        json={"expiresIn": SIGNED_URL_EXPIRY},
    )
    if r.status_code == 200:
        data = r.json()
        return f"{SUPABASE_URL}/storage/v1{data['signedURL']}"
    return None


def upload_job(job_id, job_dir, docx_path=None):
    """Upload all job files to Supabase Storage.

    Args:
        job_id: Job identifier (used as folder name in storage)
        job_dir: Local job directory
        docx_path: Optional path to the DOCX file (if different from default)

    Returns:
        dict with signed URLs for each uploaded file
    """
    if not SUPABASE_SERVICE_KEY:
        print("  Error: SUPABASE_SERVICE_ROLE_KEY not set")
        return None

    ensure_bucket()

    # Files to upload
    files = [
        ("original.pdf", os.path.join(job_dir, "input.pdf"), "application/pdf"),
        ("review_report.json", os.path.join(job_dir, "review_report.json"), "application/json"),
    ]

    # Find DOCX
    if docx_path and os.path.exists(docx_path):
        files.append(("traduccion.docx", docx_path,
                       "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))
    else:
        # Try default location
        default_docx = os.path.join(job_dir, "traduccion.docx")
        if os.path.exists(default_docx):
            files.append(("traduccion.docx", default_docx,
                           "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))

    # Upload
    print(f"  Uploading to Supabase Storage ({BUCKET}/{job_id}/)...")
    uploaded = []
    for remote_name, local_path, content_type in files:
        if upload_file(job_id, local_path, remote_name, content_type):
            uploaded.append(remote_name)

    # Generate signed URLs
    urls = {}
    for filename in uploaded:
        url = generate_signed_url(job_id, filename)
        if url:
            urls[filename] = url

    # Save URLs to job dir
    urls_path = os.path.join(job_dir, "download_urls.json")
    with open(urls_path, "w") as f:
        json.dump(urls, f, indent=2)

    print(f"  {len(uploaded)} files uploaded, URLs saved to {urls_path}")
    return urls


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    job_id = sys.argv[1]
    job_dir = os.path.join(os.path.dirname(__file__), "jobs", job_id)
    urls = upload_job(job_id, job_dir)

    if urls:
        print("\nDownload URLs (valid 7 days):")
        for name, url in urls.items():
            print(f"  {name}: {url}")
