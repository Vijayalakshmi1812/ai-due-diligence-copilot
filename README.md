# AI Due Diligence Copilot

A RAG platform that analyzes company filings (10-K, annual reports, investor decks, market reports) and produces **source-backed** risk assessments, growth opportunities and executive summaries. Every finding cites the document page it came from.

## Features
- Table-aware PDF parsing with page-level metadata
- Hybrid retrieval: BM25 + dense embeddings fused with Reciprocal Rank Fusion
- Optional cross-encoder reranking
- Structured JSON reports validated with Pydantic
- **Citation guard:** findings that are not backed by retrieved text are dropped
- Cited Q&A that answers "Insufficient evidence" when the documents don't contain the answer
- Evaluation harness: Hit@k, MRR, Precision@k and LLM-judged faithfulness
- FastAPI backend, Streamlit UI, pytest tests, GitHub Actions CI

## Architecture
```
PDFs -> pdfplumber (text + tables) -> chunks + metadata -> bge embeddings -> ChromaDB
                                                      \-> BM25 index
Query -> vector search + BM25 -> RRF fusion -> (rerank) -> LLM (Groq) -> JSON report / cited answer
```

## Setup
```bash
python -m venv venv
venv\Scripts\activate          # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env           # Windows: copy .env.example .env  -> then add your Groq API key
```
Get a free Groq key at https://console.groq.com/keys.

## Add data
Download a 10-K from SEC EDGAR (open the filing, Print -> Save as PDF) and name it
`<company>_<doctype>_<year>.pdf`, e.g. `apple_10-K_2025.pdf`. Put it in `data/`, then:
```bash
python -m scripts.ingest_folder data/
```
You can also upload PDFs from the Streamlit sidebar.

## Run
Terminal 1:
```bash
python -m uvicorn app.main:app --reload
```
Terminal 2:
```bash
python -m streamlit run ui/streamlit_app.py
```
Open http://localhost:8501.

## API
| Endpoint | Description |
|---|---|
| `POST /ingest` | Upload a PDF (`file`, `company`, `doc_type`, `year`) |
| `GET /companies` | List indexed companies |
| `GET /report/{company}` | Executive summary, risks and growth opportunities with citations |
| `GET /ask?company=...&q=...` | Cited answer to a question |
| `GET /health` | Health check |

## Evaluation

Run: `python -m evaluation.run_eval --faithfulness`

Dataset: Apple FY2025 10-K (327 chunks), 30 questions. A retrieved chunk counts as relevant if it contains
enough of the expected keywords. Faithfulness is LLM-judged: the share of claims in an answer that are
supported by the retrieved context.

| Strategy | Hit@5 | MRR | Precision@5 |
|---|---|---|---|
| Vector only | 0.93 | 0.79 | 0.53 |
| Hybrid (BM25 + vector, RRF) | 0.97 | 0.85 | 0.54 |
| Hybrid + cross-encoder rerank | 0.97 | 0.81 | 0.59 |

**Faithfulness:** 0.96 (29 of 30 questions scored; one was skipped after an API error).

**Findings:** Hybrid retrieval ranked relevant chunks higher than vector search alone (MRR 0.79 to 0.85),
and reranking gave the cleanest top results (Precision@5 0.53 to 0.59). The report generator uses hybrid
retrieval for speed; Q&A uses hybrid plus reranking. Differences are modest on a 30-question set.

**Limitations:** Keyword-based relevance is only a proxy for human judgment. Results come from a single
document. The faithfulness judge is an LLM from the same family as the answer generator, so it may be
lenient.

## Tests
```bash
python -m pytest -q
```

## Disclaimer
Outputs are AI-generated from the supplied documents and are not financial or investment advice.
Verify against the cited source pages.