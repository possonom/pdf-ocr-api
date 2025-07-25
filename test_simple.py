from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "OCR API"


def test_app_title():
    """Test app configuration"""
    assert app.title == "OCR API"
    assert app.version == "1.0.0"