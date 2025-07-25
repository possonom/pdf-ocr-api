from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pdf2image import convert_from_bytes
from pytesseract import image_to_string

app = FastAPI() 

@app.post("/ocr/pdf")
async def ocr_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return JSONResponse(status_code=400, content={"error": "Only PDF files are supported"})

    contents = await file.read()

    try:
        images = convert_from_bytes(contents, dpi=300)
        results = []
        for i, image in enumerate(images):
            text = image_to_string(image, lang="deu+fra+eng")
            results.append({"page": i + 1, "text": text.strip()})
        return {"pages": results}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})