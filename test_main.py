import pytest
import io
from fastapi.testclient import TestClient
from PIL import Image
from unittest.mock import patch, MagicMock

from main import app

client = TestClient(app)


# Test fixtures
@pytest.fixture
def sample_image():
    """Create a sample image for testing"""
    img = Image.new("RGB", (100, 100), color="white")
    img_buffer = io.BytesIO()
    img.save(img_buffer, format="PNG")
    img_buffer.seek(0)
    return img_buffer


@pytest.fixture
def sample_pdf_bytes():
    """Mock PDF bytes for testing"""
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n%%EOF"


class TestHealthCheck:
    def test_health_check_endpoint(self):
        """Test the health check endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "OCR API"}


class TestPdfToImages:
    @patch("pdf2image.convert_from_bytes")
    def test_pdf_to_images_success(self, mock_convert, sample_pdf_bytes):
        """Test successful PDF to images conversion"""
        # Mock the pdf2image response
        mock_image = MagicMock()
        mock_image.width = 100
        mock_image.height = 150

        # Mock the save method to write PNG data
        def mock_save(buffer, format):
            buffer.write(b"fake_png_data")

        mock_image.save = mock_save
        mock_convert.return_value = [mock_image]

        # Test the endpoint
        response = client.post(
            "/pdf-to-images",
            files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_pages"] == 1
        assert len(data["images"]) == 1
        assert data["images"][0]["page"] == 1
        assert data["images"][0]["format"] == "PNG"
        assert "data" in data["images"][0]

        # Verify pdf2image was called correctly
        mock_convert.assert_called_once_with(sample_pdf_bytes, dpi=200, fmt="png")

    def test_pdf_to_images_invalid_file(self):
        """Test PDF to images with invalid file type"""
        response = client.post(
            "/pdf-to-images", files={"file": ("test.txt", b"not a pdf", "text/plain")}
        )

        assert response.status_code == 400
        assert "File must be a PDF" in response.json()["detail"]

    @patch("pdf2image.convert_from_bytes")
    def test_pdf_to_images_processing_error(self, mock_convert, sample_pdf_bytes):
        """Test PDF to images conversion error handling"""
        mock_convert.side_effect = Exception("PDF processing failed")

        response = client.post(
            "/pdf-to-images",
            files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
        )

        assert response.status_code == 500
        assert "PDF conversion failed" in response.json()["detail"]


class TestExtractText:
    @patch("pytesseract.image_to_string")
    @patch("pytesseract.image_to_data")
    def test_extract_text_success(
        self, mock_image_to_data, mock_image_to_string, sample_image
    ):
        """Test successful text extraction from image"""
        # Mock tesseract responses
        mock_image_to_string.return_value = "Hello World Test"
        mock_image_to_data.return_value = {
            "text": ["Hello", "World", "Test"],
            "conf": [95, 87, 92],
            "left": [10, 50, 90],
            "top": [10, 10, 10],
            "width": [40, 40, 30],
            "height": [20, 20, 20],
        }

        response = client.post(
            "/extract-text",
            files={"file": ("test.png", sample_image.getvalue(), "image/png")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["text"] == "Hello World Test"
        assert data["language"] == "eng"
        assert data["word_count"] == 3
        assert len(data["words_with_confidence"]) == 3
        assert data["average_confidence"] > 0

        # Verify tesseract was called correctly
        mock_image_to_string.assert_called_once()
        mock_image_to_data.assert_called_once()

    @patch("pytesseract.image_to_string")
    def test_extract_text_processing_error(self, mock_image_to_string, sample_image):
        """Test OCR processing error handling"""
        mock_image_to_string.side_effect = Exception("Tesseract failed")

        response = client.post(
            "/extract-text",
            files={"file": ("test.png", sample_image.getvalue(), "image/png")},
        )

        assert response.status_code == 500
        assert "Text extraction failed" in response.json()["detail"]


class TestErrorHandling:
    def test_missing_file_parameter(self):
        """Test endpoints without file parameter"""
        response = client.post("/extract-text")
        assert response.status_code == 422  # Validation error

        response = client.post("/pdf-to-images")
        assert response.status_code == 422


# Pytest configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v"])