import pytest
import io
from fastapi.testclient import TestClient
from PIL import Image
import base64
from unittest.mock import patch, MagicMock

from main import app

client = TestClient(app)

# Test fixtures
@pytest.fixture
def sample_image():
    """Create a sample image for testing"""
    img = Image.new('RGB', (100, 100), color='white')
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
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
    @patch('pdf2image.convert_from_bytes')
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
            files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")}
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
            "/pdf-to-images",
            files={"file": ("test.txt", b"not a pdf", "text/plain")}
        )
        
        assert response.status_code == 400
        assert "File must be a PDF" in response.json()["detail"]

    @patch('pdf2image.convert_from_bytes')
    def test_pdf_to_images_processing_error(self, mock_convert, sample_pdf_bytes):
        """Test PDF to images conversion error handling"""
        mock_convert.side_effect = Exception("PDF processing failed")
        
        response = client.post(
            "/pdf-to-images", 
            files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")}
        )
        
        assert response.status_code == 500
        assert "PDF conversion failed" in response.json()["detail"]

    @patch('pdf2image.convert_from_bytes')
    def test_pdf_to_images_custom_parameters(self, mock_convert, sample_pdf_bytes):
        """Test PDF to images with custom DPI and format"""
        mock_image = MagicMock()
        mock_image.width = 200
        mock_image.height = 300
        mock_image.save = lambda buffer, format: buffer.write(b"fake_jpeg_data")
        mock_convert.return_value = [mock_image]
        
        response = client.post(
            "/pdf-to-images",
            files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
            data={"dpi": "300", "format": "JPEG"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["images"][0]["format"] == "JPEG"
        
        # Verify custom parameters were used
        mock_convert.assert_called_once_with(sample_pdf_bytes, dpi=300, fmt="jpeg")

class TestExtractText:
    @patch('pytesseract.image_to_string')
    @patch('pytesseract.image_to_data')
    def test_extract_text_success(self, mock_image_to_data, mock_image_to_string, sample_image):
        """Test successful text extraction from image"""
        # Mock tesseract responses
        mock_image_to_string.return_value = "Hello World Test"
        mock_image_to_data.return_value = {
            'text': ['Hello', 'World', 'Test'],
            'conf': [95, 87, 92],
            'left': [10, 50, 90],
            'top': [10, 10, 10],
            'width': [40, 40, 30],
            'height': [20, 20, 20]
        }
        
        response = client.post(
            "/extract-text",
            files={"file": ("test.png", sample_image.getvalue(), "image/png")}
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

    @patch('pytesseract.image_to_string')
    @patch('pytesseract.image_to_data')
    def test_extract_text_custom_language(self, mock_image_to_data, mock_image_to_string, sample_image):
        """Test text extraction with custom language"""
        mock_image_to_string.return_value = "Hola Mundo"
        mock_image_to_data.return_value = {
            'text': ['Hola', 'Mundo'],
            'conf': [90, 85],
            'left': [10, 50],
            'top': [10, 10],
            'width': [40, 50],
            'height': [20, 20]
        }
        
        response = client.post(
            "/extract-text",
            files={"file": ("test.png", sample_image.getvalue(), "image/png")},
            data={"language": "spa", "config": "--psm 6"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "spa"
        
        # Verify custom parameters were used
        args, kwargs = mock_image_to_string.call_args
        assert kwargs["lang"] == "spa"
        assert kwargs["config"] == "--psm 6"

    @patch('pytesseract.image_to_string')
    def test_extract_text_processing_error(self, mock_image_to_string, sample_image):
        """Test OCR processing error handling"""
        mock_image_to_string.side_effect = Exception("Tesseract failed")
        
        response = client.post(
            "/extract-text",
            files={"file": ("test.png", sample_image.getvalue(), "image/png")}
        )
        
        assert response.status_code == 500
        assert "Text extraction failed" in response.json()["detail"]

class TestPdfToText:
    @patch('pdf2image.convert_from_bytes')
    @patch('pytesseract.image_to_string')
    def test_pdf_to_text_success(self, mock_image_to_string, mock_convert, sample_pdf_bytes):
        """Test successful PDF to text conversion"""
        # Mock pdf2image
        mock_images = [MagicMock(), MagicMock()]
        mock_convert.return_value = mock_images
        
        # Mock tesseract for each page
        mock_image_to_string.side_effect = ["Page 1 text", "Page 2 text"]
        
        response = client.post(
            "/pdf-to-text",
            files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_pages"] == 2
        assert "Page 1 text" in data["combined_text"]
        assert "Page 2 text" in data["combined_text"]
        assert len(data["pages"]) == 2
        assert data["pages"][0]["page"] == 1
        assert data["pages"][1]["page"] == 2

    def test_pdf_to_text_invalid_file(self):
        """Test PDF to text with invalid file"""
        response = client.post(
            "/pdf-to-text",
            files={"file": ("test.txt", b"not a pdf", "text/plain")}
        )
        
        assert response.status_code == 400
        assert "File must be a PDF" in response.json()["detail"]

    @patch('pdf2image.convert_from_bytes')
    @patch('pytesseract.image_to_string')
    def test_pdf_to_text_partial_failure(self, mock_image_to_string, mock_convert, sample_pdf_bytes):
        """Test PDF to text with some pages failing OCR"""
        # Mock pdf2image
        mock_images = [MagicMock(), MagicMock()]
        mock_convert.return_value = mock_images
        
        # Mock tesseract - first succeeds, second fails
        mock_image_to_string.side_effect = ["Page 1 text", Exception("OCR failed")]
        
        response = client.post(
            "/pdf-to-text",
            files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_pages"] == 2
        assert data["pages"][0]["text"] == "Page 1 text"
        assert "error" in data["pages"][1]

class TestErrorHandling:
    def test_missing_file_parameter(self):
        """Test endpoints without file parameter"""
        response = client.post("/extract-text")
        assert response.status_code == 422  # Validation error
        
        response = client.post("/pdf-to-images")
        assert response.status_code == 422
        
        response = client.post("/pdf-to-text")
        assert response.status_code == 422

    def test_empty_file(self):
        """Test endpoints with empty files"""
        empty_file = io.BytesIO(b"")
        
        response = client.post(
            "/extract-text",
            files={"file": ("empty.png", empty_file.getvalue(), "image/png")}
        )
        assert response.status_code == 500

    @patch('PIL.Image.open')
    def test_corrupted_image(self, mock_image_open):
        """Test handling of corrupted image files"""
        mock_image_open.side_effect = Exception("Cannot identify image file")
        
        response = client.post(
            "/extract-text",
            files={"file": ("corrupt.png", b"corrupted data", "image/png")}
        )
        assert response.status_code == 500

class TestPerformance:
    @patch('pdf2image.convert_from_bytes')
    @patch('pytesseract.image_to_string')
    def test_large_pdf_handling(self, mock_image_to_string, mock_convert, sample_pdf_bytes):
        """Test handling of large PDFs (many pages)"""
        # Simulate a 10-page PDF
        mock_images = [MagicMock() for _ in range(10)]
        mock_convert.return_value = mock_images
        mock_image_to_string.return_value = "Sample text"
        
        response = client.post(
            "/pdf-to-text",
            files={"file": ("large.pdf", sample_pdf_bytes, "application/pdf")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_pages"] == 10
        assert len(data["pages"]) == 10

# Integration tests (require actual tesseract installation)
@pytest.mark.integration
class TestIntegration:
    def test_real_image_ocr(self):
        """Integration test with real image (requires tesseract)"""
        # Create a simple image with text
        img = Image.new('RGB', (200, 50), color='white')
        # Note: This would need actual text rendering for a real test
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        response = client.post(
            "/extract-text",
            files={"file": ("test.png", img_buffer.getvalue(), "image/png")}
        )
        
        # Should not fail even if no text is detected
        assert response.status_code == 200

# Pytest configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v"])