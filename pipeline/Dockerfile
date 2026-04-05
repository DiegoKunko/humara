FROM python:3.12-slim

# System deps for PyMuPDF, WeasyPrint, and fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
    libffi-dev libcairo2 fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Don't buffer Python output (see logs in real time)
ENV PYTHONUNBUFFERED=1

CMD ["python", "worker.py"]
