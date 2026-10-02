import json
import os

from pydantic import ValidationError

from app.retrieve import retrieve
from app.schemas import Report

MODEL = os.getenv("GROQ_MODEL") or "openai/gpt-oss-120b"
_client = None

QUERIES = [
    "key risk factors",
    "litigation and regulatory exposure",
    "debt, liquidity and cash flow",
    "revenue growth drivers",
    "market expansion and strategy",
    "competition and market share",
]

REPORT_SYSTEM = """You are a senior due diligence analyst.
Use ONLY the provided context. Every finding MUST cite one or more sources, copied exactly
from the bracketed tags in the context (for example: apple_10-K_2024.pdf p.23).
If the evidence is insufficient for a point, leave it out. Do not invent numbers.
Severity must be one of: High, Medium, Low.
Return ONLY valid JSON with this schema:
{"company": str, "executive_summary": str,
 "risks": [{"title": str, "severity": str, "explanation": str, "sources": [str]}],
 "growth_opportunities": [{"title": str, "severity": str, "explanation": str, "sources": [str]}]}"""

ASK_SYSTEM = """You are a due diligence analyst. Answer ONLY from the provided context.
Cite sources inline exactly as given in brackets, e.g. [apple_10-K_2024.pdf p.23].
If the context does not contain the answer, say "Insufficient evidence in the provided documents."
Be concise and precise."""


def get_llm():
    global _client
    if _client is None:
        from groq import Groq

        # Longer timeout + automatic retries for flaky connections
        _client = Groq(api_key=os.environ["GROQ_API_KEY"], timeout=90.0, max_retries=4)
    return _client


def chat(system: str, user: str, json_mode: bool = False) -> str:
    kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
    out = get_llm().chat.completions.create(
        model=MODEL,
        temperature=0.1,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        **kwargs,
    )
    return out.choices[0].message.content


def _clean_source(s: str) -> str:
    return s.strip().strip("[]").strip()


def analyze(company: str, per_query: int = 4) -> Report:
    seen, ctx, valid_sources = set(), [], set()
    for q in QUERIES:
        # "hybrid" skips the slow reranker so reports generate quickly
        for r in retrieve(f"{company} {q}", company, k=per_query, mode="hybrid"):
            if r["text"] in seen:
                continue
            seen.add(r["text"])
            valid_sources.add(r["source"])
            ctx.append(f"[{r['source']}] {r['text']}")

    if not ctx:
        raise ValueError(f"No documents found for '{company}'. Ingest filings first.")

    user = f"Company: {company}\n\nContext:\n" + "\n\n".join(ctx)
    last_err = None
    for _ in range(2):
        try:
            data = json.loads(chat(REPORT_SYSTEM, user, json_mode=True))
            data["company"] = company
            report = Report(**data)
            # Citation guard: keep only real retrieved sources, drop unsupported findings
            for field in ("risks", "growth_opportunities"):
                kept = []
                for f in getattr(report, field):
                    f.sources = [s for s in map(_clean_source, f.sources) if s in valid_sources]
                    if f.sources:
                        kept.append(f)
                setattr(report, field, kept)
            return report
        except (json.JSONDecodeError, ValidationError) as e:
            last_err = e
    raise RuntimeError(f"LLM returned invalid output: {last_err}")


def ask(question: str, company: str, k: int = 6) -> dict:
    res = retrieve(question, company, k=k)
    if not res:
        raise ValueError(f"No documents found for '{company}'. Ingest filings first.")
    ctx = "\n\n".join(f"[{r['source']}] {r['text']}" for r in res)
    answer = chat(ASK_SYSTEM, f"Context:\n{ctx}\n\nQuestion: {question}")
    return {
        "answer": answer,
        "sources": sorted({r["source"] for r in res}),
        "contexts": [r["text"] for r in res],
    }