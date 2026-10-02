import os

import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter

STORE_DIR = os.getenv("CHROMA_DIR", "store")
EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")

splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=120)
_collection = None


def norm(company: str) -> str:
    return company.strip().lower()


def get_collection():
    global _collection
    if _collection is None:
        import chromadb
        from chromadb.utils import embedding_functions

        ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
        client = chromadb.PersistentClient(path=STORE_DIR)
        _collection = client.get_or_create_collection("due_diligence", embedding_function=ef)
    return _collection


def _table_to_text(table) -> str:
    rows = []
    for row in table:
        cells = [(c or "").replace("\n", " ").strip() for c in row]
        if any(cells):
            rows.append(" | ".join(cells))
    return "\n".join(rows)


def ingest(path: str, company: str, doc_type: str, year: int) -> int:
    col = get_collection()
    name = os.path.basename(path)
    key = norm(company)
    ids, docs, metas = [], [], []

    with pdfplumber.open(path) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            try:
                for table in page.extract_tables():
                    t = _table_to_text(table)
                    if t:
                        text += "\n" + t
            except Exception:
                pass
            for i, chunk in enumerate(splitter.split_text(text)):
                ids.append(f"{key}-{name}-{pno}-{i}")
                docs.append(chunk)
                metas.append({
                    "source": f"{name} p.{pno}",
                    "company": key,
                    "doc_type": doc_type,
                    "year": int(year),
                })

    for s in range(0, len(ids), 128):
        col.upsert(ids=ids[s:s + 128], documents=docs[s:s + 128], metadatas=metas[s:s + 128])
    return len(ids)