# PDF OCR API

A FastAPI-based microservice for OCR (Optical Character Recognition) and PDF processing, designed to work seamlessly with n8n workflows and other automation tools.

## 🚀 Current Status

**Phase 2: OCR Functionality Complete** ✅
- Health check endpoint
- PDF to images conversion
- OCR text extraction from images
- Dependency checking
- Comprehensive test suite
- CI/CD pipeline with GitHub Actions
- Docker containerization

## Features

- 📄 **PDF to Images**: Convert PDF pages to high-quality images (PNG/JPEG)
- 🔍 **Text Extraction**: Extract text from images using Tesseract OCR
- 🎯 **Graceful Degradation**: Works even when OCR dependencies aren't installed
- 🌐 **RESTful API**: Easy integration with any application
- 🧪 **Comprehensive Testing**: Full test coverage with automated CI/CD
- 📊 **Health Checks**: Built-in monitoring and dependency checking
- 🐳 **Docker Ready**: Containerized for easy deployment

## Quick Start

### Using Docker (Recommended)

```bash
# Run the latest version
docker run -p 8000:8000 ghcr.io/possonom/pdf-ocr-api:latest

# Or run a specific version
docker run -p 8000:8000 ghcr.io/possonom/pdf-ocr-api:v0.0.1
```

### Local Development

```bash
# Clone the repository
git clone https://github.com/possonom/pdf-ocr-api.git
cd pdf-ocr-api

# Install dependencies
pip install -r requirements.txt

# Install system dependencies (Ubuntu/Debian)
sudo apt-get install tesseract-ocr tesseract-ocr-eng poppler-utils

# Run the application
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Test the API

```bash
# Check if the API is running
curl http://localhost:8000/

# Check available dependencies
curl http://localhost:8000/dependencies

# Test with your own files
curl -X POST -F "file=@your-image.png" http://localhost:8000/extract-text
curl -X POST -F "file=@your-document.pdf" http://localhost:8000/pdf-to-images
```

## API Endpoints

### Health Check
```http
GET /
```
Returns service status and health information.

**Response:**
```json
{
  "status": "healthy",
  "service": "OCR API"
}
```

### Check Dependencies
```http
GET /dependencies
```
Shows which OCR dependencies are available.

**Response:**
```json
{
  "dependencies": {
    "fastapi": true,
    "pdf2image": true,
    "pytesseract": true,
    "PIL": true
  }
}
```

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
  "total_pages": 2,
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
  "word_count": 42
}
```

## Error Handling

The API provides graceful error handling:

- **400 Bad Request**: Invalid file type (e.g., non-PDF for PDF endpoints)
- **422 Validation Error**: Missing required parameters
- **500 Internal Server Error**: Processing errors
- **503 Service Unavailable**: OCR dependencies not installed

## Integration with n8n

### HTTP Request Node Configuration

1. **Method**: POST
2. **URL**: `http://your-api-url/extract-text`
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
    wordCount: ocrResult.word_count,
    language: ocrResult.language,
    processedAt: new Date().toISOString()
  };
} else {
  throw new Error(`OCR processing failed: ${ocrResult.detail}`);
}
```

## Development

### Building Docker Image

```bash
# Build the image
docker build -t ghcr.io/possonom/pdf-ocr-api:v0.0.1 .

# Test locally
docker run --rm -p 8000:8000 ghcr.io/possonom/pdf-ocr-api:v0.0.1

# Push to registry
docker push ghcr.io/possonom/pdf-ocr-api:v0.0.1
```

### Running Tests

```bash
# Install test dependencies
pip install pytest httpx

# Run all tests
pytest test_main.py -v

# Run with coverage
pytest test_main.py --cov=main
```

### Code Quality

```bash
# Format code
black main.py test_main.py

# Check linting
flake8 main.py --max-line-length=88

# Sort imports
isort main.py test_main.py
```

## Dependencies

### System Requirements
- Python 3.10+
- Tesseract OCR (`tesseract-ocr`)
- Poppler Utils (`poppler-utils`)

### Python Packages
- `fastapi==0.104.1` - Web framework
- `uvicorn[standard]==0.24.0` - ASGI server
- `python-multipart==0.0.6` - File upload support
- `pdf2image==1.17.0` - PDF processing
- `pytesseract==0.3.13` - OCR functionality
- `Pillow==10.1.0` - Image processing

## Configuration

### Tesseract Languages

Default language is English (`eng`). To add more languages:

```bash
# Install additional language packs
sudo apt-get install tesseract-ocr-deu tesseract-ocr-fra tesseract-ocr-spa
```

Common language codes:
- `eng`: English
- `deu`: German  
- `fra`: French
- `spa`: Spanish

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Deployment

### Coming Soon 🚧
- Docker containerization
- Kubernetes deployment manifests
- Production-ready configuration
- Monitoring and metrics

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run tests: `pytest test_main.py`
5. Submit a pull request

### Development Workflow

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/pdf-ocr-api.git
cd pdf-ocr-api

# Install in development mode
pip install -r requirements.txt

# Run with auto-reload
uvicorn main:app --reload

# Run tests on changes
pytest test_main.py -v
```

## Troubleshooting

### Common Issues

**"Tesseract not found" Error:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-eng
```

**"Poppler not found" Error:**
```bash
sudo apt-get install poppler-utils
```

**Low OCR Accuracy:**
- Use higher DPI (300-600) for better quality
- Ensure images have good contrast
- Use appropriate language models

**Import Errors:**
```bash
# Check dependencies
curl http://localhost:8000/dependencies

# Reinstall packages
pip install -r requirements.txt
```

### Future Roadmap

#### v0.1.0 - Phase 3: Containerization
- [ ] Docker containerization
- [ ] docker-compose setup
- [ ] Container registry integration

#### v0.2.0 - Phase 4: Kubernetes Deployment  
- [ ] Kubernetes manifests
- [ ] Production configuration
- [ ] Ingress and service mesh

#### v0.3.0 - Phase 5: Enhanced Features
- [ ] PDF to text endpoint (full pipeline)
- [ ] Confidence scores and bounding boxes
- [ ] Multi-language support
- [ ] Batch processing capabilities

#### v1.0.0 - Production Ready
- [ ] Authentication and rate limiting
- [ ] Monitoring and metrics
- [ ] Performance optimization
- [ ] Production stability testing

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/possonom/pdf-ocr-api/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/possonom/pdf-ocr-api/discussions)
- 📋 **Project**: [GitHub Repository](https://github.com/possonom/pdf-ocr-api)

## Changelog

### v0.0.1 (Current - Alpha Release)
- ✅ Basic FastAPI structure
- ✅ Health check endpoint
- ✅ PDF to images conversion
- ✅ OCR text extraction
- ✅ Comprehensive test suite
- ✅ CI/CD with GitHub Actions
- ✅ Error handling and validation
- ✅ Dependencies checking