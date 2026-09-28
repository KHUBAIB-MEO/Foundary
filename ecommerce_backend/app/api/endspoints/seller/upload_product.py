from fastapi import FastAPI, HTTPException, File, UploadFile
from app.main import app


@app.post("/upload-product")
async def uploadproduct():
    pass