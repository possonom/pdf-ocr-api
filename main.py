from fastapi import FastAPI

app = FastAPI(
    title="OCR API",
    description="OCR and PDF processing service",
    version="1.0.0"
)


@app.get("/")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "OCR API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)