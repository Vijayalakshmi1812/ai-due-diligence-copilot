import os
import shutil

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

load_dotenv()

from app.analyze import analyze, ask  # noqa: E402
from app.ingest import get_collection, ingest  # noqa: E402
from app.schemas import AskResponse, Report  # noqa: E402

app = FastAPI(title="AI Due Diligence Copilot", version="1.0.0")
DATA_DIR = "data"


def _fail(e: Exception):
    """Return a readable error message to the UI instead of a bare 500."""
    msg = f"{type(e).__name__}: {e}"
    if "GROQ_API_KEY" in msg:
        msg = "GROQ_API_KEY is missing. Add it to the .env file and restart the API."
    elif "401" in msg or "invalid_api_key" in msg.lower() or "AuthenticationError" in msg:
        msg = "Groq rejected the API key. Create a new key at console.groq.com/keys, put it in .env and restart the API."
    raise HTTPException(status_code=500, detail=msg)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest")
async def ingest_doc(
    file: UploadFile = File(...),
    company: str = Form(...),
    doc_type: str = Form(...),
    year: int = Form(...),
):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, os.path.basename(file.filename))
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        chunks = ingest(path, company, doc_type, year)
    except Exception as e:
        _fail(e)
    return {"status": "ingested", "file": file.filename, "chunks": chunks}


@app.get("/companies")
def companies():
    metas = get_collection().get(include=["metadatas"])["metadatas"]
    return sorted({m["company"] for m in metas})


@app.get("/report/{company}", response_model=Report)
def report(company: str):
    try:
        return analyze(company)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        _fail(e)


@app.get("/ask", response_model=AskResponse)
def ask_question(company: str, q: str):
    try:
        res = ask(q, company)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        _fail(e)
    return {"answer": res["answer"], "sources": res["sources"]}