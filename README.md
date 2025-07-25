# OCR API Service

A FastAPI-based microservice for OCR (Optical Character Recognition) and PDF processing, designed to work seamlessly with n8n workflows and other automation tools.

## Features

- 📄 **PDF to Images**: Convert PDF pages to high-quality images
- 🔍 **Text Extraction**: Extract text from images using Tesseract OCR
- 📋 **PDF to Text**: Complete pipeline from PDF to extracted text
- 🎯 **Confidence Scores**: Get word-level confidence scores for OCR results
- 🌐 **RESTful API**: Easy integration with any application
- 🐳 **Docker Ready**: Containerized for easy deployment
- ☸️ **Kubernetes Native**: Includes K8s deployment manifests
- 📊 **Health Checks**: Built-in monitoring and health endpoints

## Quick Start

### Using Docker

```bash
# Build the image
docker build -t ocr-api:latest .

# Run the container
docker run -p 8000:8000 ocr-api:latest
```

### Using Docker Compose

```yaml
version: '3.8'
services:
  ocr-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Install system dependencies (Ubuntu/Debian)
sudo apt-get install tesseract-ocr tesseract-ocr-eng poppler-utils

# Run the application
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### Health Check
```http
GET /
```
Returns service status and health information.

### PDF to Images
```http
POST /pdf-to-images
Content-Type: multipart/form-data

file: [PDF file]
dpi: 200 (optional)
format: PNG (optional, PNG|JPEG)
```

**Response:**
```json
{
  "success": true,
  "total_pages": 3,
  "images": [
    {
      "page": 1,
      "format": "PNG",
      "data": "base64-encoded-image-data",
      "size": {"width": 1653, "height": 2338}
    }
  ]
}
```

### Extract Text from Image
```http
POST /extract-text
Content-Type: multipart/form-data

file: [Image file]
language: eng (optional)
config: --psm 6 (optional, tesseract config)
```

**Response:**
```json
{
  "success": true,
  "text": "Extracted text content...",
  "language": "eng",
  "word_count": 150,
  "words_with_confidence": [
    {
      "text": "Hello",
      "confidence": 95,
      "bbox": {"left": 100, "top": 50, "width": 60, "height": 20}
    }
  ],
  "average_confidence": 87.5
}
```

### PDF to Text (Full Pipeline)
```http
POST /pdf-to-text
Content-Type: multipart/form-data

file: [PDF file]
language: eng (optional)
dpi: 300 (optional)
```

**Response:**
```json
{
  "success": true,
  "total_pages": 3,
  "combined_text": "Full extracted text from all pages...",
  "total_words": 450,
  "pages": [
    {
      "page": 1,
      "text": "Text from page 1...",
      "word_count": 150
    }
  ]
}
```

## Kubernetes Deployment

### Deploy to Kubernetes

```bash
# Apply the deployment
kubectl apply -f k8s-deployment.yaml

# Check status
kubectl get pods -n n8n -l app=ocr-api
kubectl get svc -n n8n ocr-api-service
```

### Scale the deployment

```bash
# Scale to 5 replicas
kubectl scale deployment ocr-api -n n8n --replicas=5
```

## Integration with n8n

### HTTP Request Node Configuration

1. **Method**: POST
2. **URL**: `http://ocr-api-service/extract-text` (internal cluster URL)
3. **Body Type**: Form-Data
4. **Add Parameter**: 
   - Name: `file`
   - Type: File
   - Value: `{{ $binary.data }}`

### Processing Response in Code Node

```javascript
// Get the OCR result
const ocrResult = $input.all()[0].json;

if (ocrResult.success) {
  return {
    extractedText: ocrResult.text,
    confidence: ocrResult.average_confidence,
    wordCount: ocrResult.word_count,
    processedAt: new Date().toISOString(),
    pages: ocrResult.pages || null
  };
} else {
  throw new Error(`OCR processing failed: ${ocrResult.detail}`);
}
```

### Example n8n Workflow

```json
{
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [240, 300]
    },
    {
      "name": "OCR Processing",
      "type": "n8n-nodes-base.httpRequest",
      "position": [460, 300],
      "parameters": {
        "url": "http://ocr-api-service/extract-text",
        "method": "POST",
        "sendBinaryData": true,
        "binaryPropertyName": "file"
      }
    },
    {
      "name": "Process Results",
      "type": "n8n-nodes-base.code",
      "position": [680, 300]
    }
  ]
}
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PYTHONUNBUFFERED` | `1` | Ensure Python output is not buffered |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Tesseract Configuration

The service supports custom Tesseract configurations via the `config` parameter:

- `--psm 6`: Assume a uniform block of text
- `--psm 8`: Treat as single word
- `--oem 3`: Use default OCR Engine Mode
- `-c tessedit_char_whitelist=0123456789`: Only recognize digits

### Supported Languages

Default language is English (`eng`). To add more languages:

```dockerfile
# Add to Dockerfile
RUN apt-get install -y tesseract-ocr-deu tesseract-ocr-fra tesseract-ocr-spa
```

Common language codes:
- `eng`: English
- `deu`: German  
- `fra`: French
- `spa`: Spanish
- `chi_sim`: Chinese Simplified

## Performance Considerations

### Resource Requirements

**Minimum:**
- CPU: 250m
- Memory: 512Mi

**Recommended:**
- CPU: 500m-1000m
- Memory: 1Gi-2Gi

### Optimization Tips

1. **DPI Settings**: Higher DPI improves accuracy but increases processing time
   - Document scanning: 300 DPI
   - General use: 200 DPI
   - Fast processing: 150 DPI

2. **Image Preprocessing**: Clean images before OCR for better results
3. **Language Models**: Only install needed language packs
4. **Caching**: Consider implementing Redis caching for repeated documents

## Monitoring

### Health Checks

The service includes built-in health checks:

```bash
# Check service health
curl http://localhost:8000/

# Kubernetes health check
kubectl get pods -n n8n -l app=ocr-api
```

### Metrics

For production deployments, consider adding:
- Prometheus metrics endpoint
- Request/response time tracking
- Error rate monitoring
- Queue depth monitoring

## Troubleshooting

### Common Issues

**"Tesseract not found" Error:**
```bash
# Install tesseract
apt-get install tesseract-ocr tesseract-ocr-eng
```

**"Poppler not found" Error:**
```bash
# Install poppler utilities
apt-get install poppler-utils
```

**Low OCR Accuracy:**
- Increase DPI (try 300-600)
- Preprocess images (contrast, noise reduction)
- Use appropriate PSM mode
- Ensure correct language model

**Memory Issues:**
- Reduce concurrent requests
- Increase memory limits in Kubernetes
- Process large PDFs in chunks

### Debug Mode

```bash
# Run with debug logging
LOG_LEVEL=DEBUG uvicorn main:app --host 0.0.0.0 --port 8000
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run tests: `pytest`
5. Submit a pull request

### Development Setup

```bash
# Clone repository
git clone https://github.com/possonom/ocr-api.git
cd ocr-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install development dependencies
pip install -r requirements.txt
pip install pytest httpx

# Run tests
pytest

# Run with auto-reload
uvicorn main:app --reload
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/possonom/ocr-api/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/possonom/ocr-api/discussions)
- 📧 **Email**: support@your-domain.com

## Changelog

### v1.0.0
- Initial release
- PDF to images conversion
- OCR text extraction
- Kubernetes deployment support
- n8n integration examples