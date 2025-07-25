FROM python:3.11-alpine

RUN apk add --no-cache \
    tesseract-ocr \
    tesseract-ocr-data-deu \
    tesseract-ocr-data-fra \
    tesseract-ocr-data-eng \
    poppler-utils \
    && pip install --no-cache-dir fastapi uvicorn pdf2image pytesseract Pillow

COPY main.py /app/main.py
WORKDIR /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
