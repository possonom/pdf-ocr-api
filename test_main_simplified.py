import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "OCR API"


def test_pdf_endpoint_exists():
    """Test that PDF endpoint exists and returns validation error for missing file"""
    response = client.post("/pdf-to-images")
    assert response.status_code == 422  # Validation error for missing file
    

def test_extract_text_endpoint_exists():
    """Test that extract text endpoint exists and returns validation error for missing file"""
    response = client.post("/extract-text")
    assert response.status_code == 422  # Validation error for missing file


def test_pdf_to_text_endpoint_exists():
    """Test that PDF to text endpoint exists and returns validation error for missing file"""
    response = client.post("/pdf-to-text")
    assert response.status_code == 422  # Validation error for missing file


def test_invalid_file_type():
    """Test PDF endpoints with invalid file type"""
    response = client.post(
        "/pdf-to-images",
        files={"file": ("test.txt", b"not a pdf", "text/plain")}
    )
    assert response.status_code == 400
    assert "File must be a PDF" in response.json()["detail"]
    
    response = client.post(
        "/pdf-to-text", 
        files={"file": ("test.txt", b"not a pdf", "text/plain")}
    )
    assert response.status_code == 400
    assert "File must be a PDF" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])