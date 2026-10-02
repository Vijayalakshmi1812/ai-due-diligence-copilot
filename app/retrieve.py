import os
import re
from typing import Dict, List

from rank_bm25 import BM25Okapi

from app.ingest import get_collection, norm

RERANK_MODEL = os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
MODES = ("vector", "hybrid", "hybrid_rerank")
RERANK_CANDIDATES = 15

_reranker = None
_bm25_cache: Dict[str, dict] = {}


def get_reranker():
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder

        _reranker = CrossEncoder(RERANK_MODEL)
    return _reranker


def _tokenize(text: str) -> List[str]:
    return re.findall(r"\w+", text.lower())


def _bm25_index(company: str):
    col = get_collection()
    count = col.count()
    cached = _bm25_cache.get(company)
    if cached and cached["count"] == count:
        return cached
    got = col.get(where={"company": company}, include=["documents", "metadatas"])
    docs, metas = got["documents"], got["metadatas"]
    if not docs:
        return None
    entry = {
        "count": count,
        "docs": docs,
        "metas": metas,
        "bm25": BM25Okapi([_tokenize(d) for d in docs]),
    }
    _bm25_cache[company] = entry
    return entry


def vector_search(query: str, company: str, n: int = 20) -> List[dict]:
    col = get_collection()
    res = col.query(query_texts=[query], n_results=n, where={"company": company})
    return [
        {"text": d, "source": m["source"]}
        for d, m in zip(res["documents"][0], res["metadatas"][0])
    ]


def bm25_search(query: str, company: str, n: int = 20) -> List[dict]:
    idx = _bm25_index(company)
    if idx is None:
        return []
    scores = idx["bm25"].get_scores(_tokenize(query))
    top = sorted(range(len(scores)), key=lambda i: -scores[i])[:n]
    return [
        {"text": idx["docs"][i], "source": idx["metas"][i]["source"]}
        for i in top
        if scores[i] > 0
    ]


def _rrf(*ranked_lists: List[dict], k: int = 60) -> List[dict]:
    scores, items = {}, {}
    for lst in ranked_lists:
        for rank, item in enumerate(lst):
            key = item["text"]
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
            items[key] = item
    return [items[key] for key in sorted(scores, key=scores.get, reverse=True)]


def retrieve(query: str, company: str, k: int = 8, mode: str = "hybrid_rerank") -> List[dict]:
    """
    mode:
      vector         - dense retrieval only (baseline)
      hybrid         - BM25 + dense fused with RRF
      hybrid_rerank  - hybrid + cross-encoder reranking (default)
    """
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    company = norm(company)

    vec = vector_search(query, company)
    if mode == "vector":
        return vec[:k]

    fused = _rrf(vec, bm25_search(query, company))
    if mode == "hybrid" or not fused:
        return fused[:k]

    cands = fused[:RERANK_CANDIDATES]
    scores = get_reranker().predict([(query, c["text"]) for c in cands])
    ranked = sorted(zip(cands, scores), key=lambda x: -x[1])
    return [c for c, _ in ranked[:k]]