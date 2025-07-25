# PDF OCR API

pdf-ocr-api is a lightweight FastAPI-based service that performs OCR (Optical Character Recognition) on PDF documents. It converts PDF pages into images and extracts text using Tesseract OCR with support for multiple languages (English, German, French). Designed for containerized environments, it’s ideal for integrating with automation tools like n8n, Zapier, or other backend systems via REST API.


## Features
- Accepts PDF uploads
- Converts pages to images
- Extracts text using Tesseract in English, German, and French
- Returns structured JSON with page-wise results

## Requirements
- Docker
- Tesseract (installed via Dockerfile)

## Usage
```bash
curl -F 'file=@sample.pdf' http://localhost:8080/ocr/pdf
```

## Run with Docker
```bash
docker build -t pdf-ocr-api .
docker run -p 8080:8080 pdf-ocr-api
```

## License
MIT License

