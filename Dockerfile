FROM --platform=linux/amd64 python:3.10-slim as builder

WORKDIR /app

RUN apt-get update --fix-missing && apt-get install -y --no-install-recommends gcc g++ build-essential

COPY requirements.txt .

RUN python -m venv /venv && \
    /venv/bin/pip install --upgrade pip && \
    /venv/bin/pip install --no-cache-dir --prefer-binary -r requirements.txt

# --- Final image ---
FROM --platform=linux/amd64 python:3.10-slim

WORKDIR /app

COPY --from=builder /venv /venv

ENV PATH="/venv/bin:$PATH"

COPY process_pdfs.py .
COPY pdf_loader.py .
COPY heading_detector.py .
COPY outline_builder.py .
COPY requirements.txt .
COPY README.md .


RUN mkdir -p /output /debug_output /logs

ENV OUTPUT_DIR=/output
ENV DEBUG_DIR=/debug_output
ENV LOG_DIR=/logs

CMD ["python", "process_pdfs.py"]