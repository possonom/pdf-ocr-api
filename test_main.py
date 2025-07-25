import pytest
from fastapi.testclient import TestClient
from main import app

# Create client instance
client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "OCR API"


def test_dependencies_endpoint():
    """Test dependencies check endpoint"""
    response = client.get("/dependencies")
    assert response.status_code == 200
    data = response.json()
    assert "dependencies" in data
    assert data["dependencies"]["fastapi"] is True


def test_pdf_endpoint_without_file():
    """Test PDF endpoint returns validation error without file"""
    response = client.post("/pdf-to-images")
    assert response.status_code == 422  # Validation error


def test_ocr_endpoint_without_file():
    """Test OCR endpoint returns validation error without file"""
    response = client.post("/extract-text")
    assert response.status_code == 422  # Validation error


def test_pdf_endpoint_with_invalid_file():
    """Test PDF endpoint with non-PDF file"""
    response = client.post(
        "/pdf-to-images",
        files={"file": ("test.txt", b"not a pdf", "text/plain")}
    )
    assert response.status_code == 400
    assert "File must be a PDF" in response.json()["detail"]


def test_ocr_endpoint_with_invalid_image():
    """Test OCR endpoint with invalid image data"""
    response = client.post(
        "/extract-text",
        files={"file": ("test.png", b"not an image", "image/png")}
    )
    # Should return 503 (service unavailable) if dependencies missing
    # or 500 (server error) if dependencies present but image invalid
    assert response.status_code in [500, 503]


@pytest.mark.skipif(
    True,  # Skip by default - only run when dependencies are confirmed installed
    reason="Requires OCR dependencies to be installed"
)
def test_ocr_with_real_image():
    """Integration test with actual image (requires dependencies)"""
    from PIL import Image
    import io
    
    # Create a simple white image
    img = Image.new('RGB', (100, 50), color='white')
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    response = client.post(
        "/extract-text",
        files={"file": ("test.png", img_buffer.getvalue(), "image/png")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "text" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])