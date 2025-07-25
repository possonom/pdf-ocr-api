from fastapi import FastAPI, UploadFile, File, HTTPException
import io
import base64
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OCR API",
    description="OCR and PDF processing service",
    version="0.0.1"
)


@app.get("/")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "OCR API"}


@app.post("/pdf-to-images")
async def pdf_to_images(
    file: UploadFile = File(...), 
    dpi: int = 200, 
    format: str = "PNG"
):
    """Convert PDF to images"""
    # Check file type first, before any processing
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        # Import here to avoid issues if not installed
        import pdf2image
        
        pdf_bytes = await file.read()
        images = pdf2image.convert_from_bytes(pdf_bytes, dpi=dpi, fmt=format.lower())
        
        result_images = []
        for i, image in enumerate(images):
            img_buffer = io.BytesIO()
            image.save(img_buffer, format=format)
            img_bytes = img_buffer.getvalue()
            img_base64 = base64.b64encode(img_bytes).decode("utf-8")
            
            result_images.append({
                "page": i + 1,
                "format": format,
                "data": img_base64,
                "size": {"width": image.width, "height": image.height}
            })
        
        return {"success": True, "total_pages": len(images), "images": result_images}
        
    except ImportError:
        raise HTTPException(
            status_code=503, 
            detail="PDF processing not available - pdf2image not installed"
        )
    except Exception as e:
        logger.error(f"PDF conversion error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF conversion failed: {str(e)}")


@app.post("/extract-text")
async def extract_text(
    file: UploadFile = File(...),
    language: str = "eng",
    config: Optional[str] = None
):
    """Extract text from image using OCR"""
    try:
        # Import here to avoid issues if not installed
        import pytesseract
        from PIL import Image
        
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        text = pytesseract.image_to_string(image, lang=language, config=config or "")
        
        return {
            "success": True,
            "text": text.strip(),
            "language": language,
            "word_count": len(text.split())
        }
        
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="OCR not available - pytesseract or PIL not installed"
        )
    except Exception as e:
        logger.error(f"OCR extraction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")


@app.get("/dependencies")
def check_dependencies():
    """Check which dependencies are available"""
    deps = {"fastapi": True}  # We know this works
    
    try:
        import pdf2image
        deps["pdf2image"] = True
    except ImportError:
        deps["pdf2image"] = False
    
    try:
        import pytesseract
        deps["pytesseract"] = True
    except ImportError:
        deps["pytesseract"] = False
    
    try:
        from PIL import Image
        deps["PIL"] = True
    except ImportError:
        deps["PIL"] = False
    
    return {"dependencies": deps}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)