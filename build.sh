#!/bin/bash

# Build the Docker image
echo "Building OCR API v0.0.1..."
docker build -t ghcr.io/possonom/ocr-api:v0.0.1 .

# Tag as latest for convenience
docker tag ghcr.io/possonom/ocr-api:v0.0.1 ghcr.io/possonom/ocr-api:latest

# Test the image locally
echo "Testing image locally..."
docker run --rm -d -p 8000:8000 --name ocr-api-test ghcr.io/possonom/ocr-api:v0.0.1

# Wait for startup
sleep 10

# Test health check
echo "Testing health endpoint..."
curl -f http://localhost:8000/ || echo "Health check failed"

# Test dependencies endpoint
echo "Testing dependencies endpoint..."
curl -f http://localhost:8000/dependencies || echo "Dependencies check failed"

# Stop test container
docker stop ocr-api-test

echo "Build complete! Ready to push:"
echo "docker push ghcr.io/possonom/ocr-api:v0.0.1"
echo "docker push ghcr.io/possonom/ocr-api:latest"