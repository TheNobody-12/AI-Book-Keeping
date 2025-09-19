from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import uuid

from . import extract as extract_mod
from . import categorize as categorize_mod


class CategorizeRequest(BaseModel):
    transactions: List[Dict[str, Any]]
    categories: Optional[List[str]] = None
    use_llm: bool = False


class CategorizeResponseItem(BaseModel):
    category: str
    confidence: float
    rationale: Optional[str] = None


class CategorizeResponse(BaseModel):
    results: List[CategorizeResponseItem]


UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


app = FastAPI(title="AI Book Keeping API", version="0.1.0")

# Allow local dev from common front-end ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)) -> Dict[str, str]:
    if file is None:
        raise HTTPException(status_code=400, detail="File is required")
    file_id = str(uuid.uuid4())
    # Save as-is locally (for MVP). Replace with Azure Blob in production.
    dest_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    data = await file.read()
    with open(dest_path, "wb") as f:
        f.write(data)
    return {"file_id": file_id, "filename": file.filename}


@app.post("/extract/{file_id}")
def extract(file_id: str) -> Dict[str, Any]:
    # Find the first file matching file_id prefix (MVP approach)
    matches = [f for f in os.listdir(UPLOAD_DIR) if f.startswith(file_id + "_")]
    if not matches:
        raise HTTPException(status_code=404, detail="File not found")
    file_path = os.path.join(UPLOAD_DIR, matches[0])
    transactions = extract_mod.extract_transactions(file_path)
    return {"file_id": file_id, "transactions": transactions}


@app.post("/categorize", response_model=CategorizeResponse)
def categorize(req: CategorizeRequest) -> CategorizeResponse:
    results = categorize_mod.categorize_transactions(
        req.transactions, categories=req.categories, use_llm=req.use_llm
    )
    response_items = [CategorizeResponseItem(**r) for r in results]
    return CategorizeResponse(results=response_items)


# To run locally:
#   uvicorn AI-Book-Keeping.backend.main:app --reload

