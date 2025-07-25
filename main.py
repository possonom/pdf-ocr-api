from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import pdf2image
import pytesseract
from PIL import Image
import io
import base64
from typing import List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OCR & PDF Processing API",
    description="API service for OCR text extraction and PDF to image conversion",
    version="1.0.0"
)

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "OCR API"}

@app.post("/pdf-to-images")
async def pdf_to_images(
    file: UploadFile = File(...),
    dpi: int = 200,
    format: str = "PNG"
):
    """
    Convert PDF to images
    
    Args:
        file: PDF file to convert
        dpi: Resolution for conversion (default: 200)
        format: Output format (PNG, JPEG)
    
    Returns:
        List of base64-encoded images
    """
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        # Read PDF file
        pdf_bytes = await file.read()
        
        # Convert PDF to images
        images = pdf2image.convert_from_bytes(
            pdf_bytes,
            dpi=dpi,
            fmt=format.lower()
        )
        
        # Convert images to base64
        result_images = []
        for i, image in enumerate(images):
            # Convert PIL image to bytes
            img_buffer = io.BytesIO()
            image.save(img_buffer, format=format)
            img_bytes = img_buffer.getvalue()
            
            # Encode to base64
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            result_images.append({
                "page": i + 1,
                "format": format,
                "data": img_base64,
                "size": {"width": image.width, "height": image.height}
            })
        
        return {
            "success": True,
            "total_pages": len(images),
            "images": result_images
        }
        
    except Exception as e:
        logger.error(f"PDF conversion error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF conversion failed: {str(e)}")

@app.post("/extract-text")
async def extract_text(
    file: UploadFile = File(...),
    language: str = "eng",
    config: Optional[str] = None
):
    """
    Extract text from image using OCR
    
    Args:
        file: Image file (PNG, JPEG, etc.)
        language: Tesseract language code (default: eng)
        config: Custom tesseract configuration
    
    Returns:
        Extracted text and confidence scores
    """
    try:
        # Read image file
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Extract text
        text = pytesseract.image_to_string(
            image, 
            lang=language,
            config=config or ''
        )
        
        # Get detailed data with confidence scores
        data = pytesseract.image_to_data(
            image, 
            lang=language,
            config=config or '',
            output_type=pytesseract.Output.DICT
        )
        
        # Process confidence data
        words_with_confidence = []
        for i in range(len(data['text'])):
            if int(data['conf'][i]) > 0:  # Only include words with confidence > 0
                words_with_confidence.append({
                    "text": data['text'][i],
                    "confidence": int(data['conf'][i]),
                    "bbox": {
                        "left": data['left'][i],
                        "top": data['top'][i], 
                        "width": data['width'][i],
                        "height": data['height'][i]
                    }
                })
        
        return {
            "success": True,
            "text": text.strip(),
            "language": language,
            "word_count": len(text.split()),
            "words_with_confidence": words_with_confidence,
            "average_confidence": sum(w['confidence'] for w in words_with_confidence) / len(words_with_confidence) if words_with_confidence else 0
        }
        
    except Exception as e:
        logger.error(f"OCR extraction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")

@app.post("/pdf-to-text")
async def pdf_to_text(
    file: UploadFile = File(...),
    language: str = "eng",
    dpi: int = 300
):
    """
    Extract text from PDF by converting to images first, then OCR
    
    Args:
        file: PDF file
        language: Tesseract language code
        dpi: Resolution for PDF to image conversion
    
    Returns:
        Extracted text from all pages
    """
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        # Read PDF file
        pdf_bytes = await file.read()
        
        # Convert PDF to images
        images = pdf2image.convert_from_bytes(pdf_bytes, dpi=dpi)
        
        # Extract text from each image
        all_text = []
        page_results = []
        
        for i, image in enumerate(images):
            try:
                page_text = pytesseract.image_to_string(image, lang=language)
                all_text.append(page_text)
                
                page_results.append({
                    "page": i + 1,
                    "text": page_text.strip(),
                    "word_count": len(page_text.split())
                })
            except Exception as page_error:
                logger.warning(f"Failed to process page {i+1}: {str(page_error)}")
                page_results.append({
                    "page": i + 1,
                    "text": "",
                    "error": str(page_error)
                })
        
        # Combine all text
        combined_text = "\n\n".join(all_text)
        
        return {
            "success": True,
            "total_pages": len(images),
            "combined_text": combined_text,
            "total_words": len(combined_text.split()),
            "pages": page_results
        }
        
    except Exception as e:
        logger.error(f"PDF to text error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF text extraction failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)