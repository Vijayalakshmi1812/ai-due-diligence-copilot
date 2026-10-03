import html
import os

import requests
import streamlit as st

API = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Due Diligence Copilot", page_icon="◈", layout="wide")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --bg:#0B0F14; --panel:#111823; --panel2:#0D131B; --line:#1F2B3B;
  --text:#E6EDF3; --muted:#8A9BB0; --accent:#7CFFCB; --accent2:#5B8CFF;
  --high:#FF5C7A; --med:#FFB454; --low:#4ADE80;
}

html, body, .stApp, .stMarkdown, [data-testid="stSidebar"],
.stTextInput input, .stNumberInput input, .stSelectbox, .stButton button {
  font-family: 'Space Grotesk', sans-serif;
}
.stApp {
  background:
    radial-gradient(1100px 560px at 88% -10%, rgba(91,140,255,.14), transparent 60%),
    radial-gradient(900px 520px at -8% 8%, rgba(124,255,203,.09), transparent 55%),
    var(--bg);
  color: var(--text);
}
.block-container { padding-top: 2.2rem; max-width: 1200px; }
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

/* hero */
.hero { padding: 6px 0 22px 0; }
.eyebrow { font-family:'JetBrains Mono',monospace; font-size:12px; letter-spacing:.18em; color:var(--accent); margin-bottom:10px; }
.hero h1 { font-size:54px; line-height:1.05; font-weight:700; margin:0; letter-spacing:-.02em; color:var(--text); }
.hero h1 span { background:linear-gradient(90deg,var(--accent),var(--accent2)); -webkit-background-clip:text; background-clip:text; color:transparent; }
.hero p { color:var(--muted); font-size:17px; margin:12px 0 0 0; }

/* sidebar */
[data-testid="stSidebar"] { background: var(--panel2); border-right: 1px solid var(--line); }
.brand { font-size:20px; font-weight:700; letter-spacing:-.01em; margin-bottom:4px; }
.brand .logo { color:var(--accent); margin-right:6px; }
.side-label { font-family:'JetBrains Mono',monospace; font-size:11px; letter-spacing:.16em; color:var(--muted); margin:18px 0 8px 0; }

/* inputs */
.stTextInput input, .stNumberInput input {
  background: var(--panel) !important; color: var(--text) !important;
  border: 1px solid var(--line) !important; border-radius: 10px !important;
}
.stTextInput input:focus { border-color: var(--accent) !important; box-shadow: 0 0 0 1px var(--accent) !important; }
[data-baseweb="select"] > div { background: var(--panel) !important; border: 1px solid var(--line) !important; border-radius: 10px !important; }
[data-testid="stFileUploaderDropzone"] { background: var(--panel) !important; border: 1px dashed #2A3A50 !important; border-radius: 12px !important; }

/* buttons */
.stButton button, .stDownloadButton button {
  border-radius: 10px; border: 1px solid var(--line); background: var(--panel); color: var(--text);
  font-weight: 500; transition: all .15s ease;
}
.stButton button:hover, .stDownloadButton button:hover { border-color: var(--accent); color: var(--accent); transform: translateY(-1px); }
.stButton button[kind="primary"], [data-testid="stBaseButton-primary"] {
  background: linear-gradient(90deg, var(--accent), var(--accent2)) !important;
  color: #04110C !important; border: none !important; font-weight: 700 !important;
}
.stButton button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover { filter: brightness(1.08); color:#04110C !important; }

/* tabs */
.stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] { color: var(--muted); font-family:'JetBrains Mono',monospace; font-size:13px; letter-spacing:.06em; padding: 10px 14px; }
.stTabs [aria-selected="true"] { color: var(--accent) !important; }
.stTabs [data-baseweb="tab-highlight"] { background: var(--accent) !important; }

/* stat tiles */
.tiles { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin:18px 0 6px 0; }
.tile { background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:16px 18px; }
.tile-v { font-size:34px; font-weight:700; letter-spacing:-.02em; }
.tile-l { font-family:'JetBrains Mono',monospace; font-size:11px; letter-spacing:.14em; color:var(--muted); margin-top:2px; }
.tile.hi .tile-v { color: var(--high); }
.tile.gr .tile-v { color: var(--accent); }

/* sections */
.section-label { font-family:'JetBrains Mono',monospace; font-size:12px; letter-spacing:.18em; color:var(--muted); margin:26px 0 10px 0; display:flex; align-items:center; gap:8px; }
.section-label::before { content:""; width:8px; height:8px; border-radius:50%; background:var(--accent2); }
.section-label.risk::before { background: var(--high); }
.section-label.grow::before { background: var(--accent); }
.summary { background:linear-gradient(180deg,var(--panel),var(--panel2)); border:1px solid var(--line); border-radius:14px; padding:20px 22px; font-size:17px; line-height:1.65; }

/* finding cards */
.card { background:var(--panel); border:1px solid var(--line); border-left:4px solid var(--med); border-radius:12px; padding:16px 18px; margin-bottom:12px; transition:transform .15s ease, border-color .15s ease; }
.card:hover { transform: translateY(-2px); border-color:#2C3E57; }
.card.high { border-left-color: var(--high); }
.card.low { border-left-color: var(--low); }
.card-top { display:flex; align-items:center; gap:10px; margin-bottom:8px; }
.card-title { font-weight:600; font-size:16px; }
.card p { color:#B8C4D2; font-size:14.5px; line-height:1.6; margin:0 0 10px 0; }
.pill { font-family:'JetBrains Mono',monospace; font-size:10.5px; letter-spacing:.12em; padding:3px 8px; border-radius:999px; font-weight:500; }
.pill.high { background:rgba(255,92,122,.15); color:var(--high); }
.pill.med { background:rgba(255,180,84,.15); color:var(--med); }
.pill.low { background:rgba(74,222,128,.15); color:var(--low); }
.chips { display:flex; flex-wrap:wrap; gap:6px; }
.chip { font-family:'JetBrains Mono',monospace; font-size:11px; color:var(--accent); background:rgba(124,255,203,.07); border:1px solid rgba(124,255,203,.22); border-radius:6px; padding:2px 8px; }

/* answer */
.answer { background:var(--panel); border:1px solid var(--line); border-left:4px solid var(--accent); border-radius:12px; padding:18px 20px; font-size:16px; line-height:1.65; margin:14px 0 10px 0; }
.empty { color:var(--muted); font-size:14px; padding:14px 0; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

SEV_ORDER = {"high": 0, "medium": 1, "low": 2}
SEV_CLASS = {"high": "high", "medium": "med", "low": "low"}
SUGGESTIONS = [
    "What are the main supply chain risks?",
    "What is the debt and liquidity position?",
    "What legal proceedings does the company face?",
    "How does the company return capital to shareholders?",
]


def esc(text) -> str:
    """Escape text for safe HTML (also stops '$' being rendered as LaTeX)."""
    return html.escape(str(text)).replace("\n", " ").replace("$", "&#36;")


def err_text(r) -> str:
    try:
        return str(r.json().get("detail", r.text))
    except Exception:
        return r.text or f"HTTP {r.status_code}"


def chips(sources) -> str:
    return "".join(f'<span class="chip">{esc(s)}</span>' for s in sources)


def card(x) -> str:
    sev = x["severity"].strip().lower()
    cls = SEV_CLASS.get(sev, "med")
    return (
        f'<div class="card {cls}"><div class="card-top">'
        f'<span class="pill {cls}">{esc(x["severity"]).upper()}</span>'
        f'<span class="card-title">{esc(x["title"])}</span></div>'
        f'<p>{esc(x["explanation"])}</p>'
        f'<div class="chips">{chips(x["sources"])}</div></div>'
    )


def tile(label, value, cls="") -> str:
    return f'<div class="tile {cls}"><div class="tile-v">{value}</div><div class="tile-l">{label}</div></div>'


def report_markdown(rep) -> str:
    lines = [f"# Due Diligence Report: {rep['company']}", "", "## Executive Summary", rep["executive_summary"], ""]
    for title, key in [("Risks", "risks"), ("Growth Opportunities", "growth_opportunities")]:
        lines += [f"## {title}", ""]
        for x in rep[key]:
            lines.append(f"### {x['title']} ({x['severity']})")
            lines.append(x["explanation"])
            lines.append("Sources: " + ", ".join(x["sources"]))
            lines.append("")
    return "\n".join(lines)


def render_report(rep):
    by_sev = lambda x: SEV_ORDER.get(x["severity"].strip().lower(), 1)
    risks = sorted(rep["risks"], key=by_sev)
    growth = sorted(rep["growth_opportunities"], key=by_sev)
    high = sum(1 for r in risks if r["severity"].strip().lower() == "high")
    pages = {s for x in risks + growth for s in x["sources"]}

    st.markdown(
        '<div class="tiles">'
        + tile("RISKS FLAGGED", len(risks))
        + tile("HIGH SEVERITY", high, "hi")
        + tile("GROWTH IDEAS", len(growth), "gr")
        + tile("PAGES CITED", len(pages))
        + "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-label">EXECUTIVE SUMMARY</div>'
        f'<div class="summary">{esc(rep["executive_summary"])}</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown('<div class="section-label risk">RISKS</div>', unsafe_allow_html=True)
        st.markdown("".join(card(x) for x in risks) or '<div class="empty">No well-supported findings.</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="section-label grow">GROWTH OPPORTUNITIES</div>', unsafe_allow_html=True)
        st.markdown("".join(card(x) for x in growth) or '<div class="empty">No well-supported findings.</div>', unsafe_allow_html=True)

    st.download_button(
        "Download report (.md)",
        report_markdown(rep),
        file_name=f"{rep['company']}_due_diligence.md",
        mime="text/markdown",
    )


# ---------------- Sidebar ----------------
try:
    companies = requests.get(f"{API}/companies", timeout=30).json()
    api_ok = True
except Exception:
    companies, api_ok = [], False

with st.sidebar:
    st.markdown('<div class="brand"><span class="logo">◈</span>DD Copilot</div>', unsafe_allow_html=True)
    st.markdown('<div class="side-label">INDEXED COMPANIES</div>', unsafe_allow_html=True)
    if companies:
        st.markdown(f'<div class="chips">{chips(companies)}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty">None yet</div>', unsafe_allow_html=True)

    st.markdown('<div class="side-label">ADD DOCUMENTS</div>', unsafe_allow_html=True)
    f = st.file_uploader("PDF filing, statement, deck or report", type="pdf")
    company_in = st.text_input("Company name")
    dtype = st.selectbox("Document type", ["10-K", "10-Q", "Annual Report", "Financial Statement", "Investor Deck", "Market Report"])
    year = st.number_input("Year", 2000, 2030, 2025)
    if st.button("Ingest document", use_container_width=True):
        if not f or not company_in:
            st.warning("Upload a PDF and enter a company name.")
        else:
            with st.spinner("Parsing and indexing..."):
                r = requests.post(
                    f"{API}/ingest",
                    files={"file": (f.name, f.getvalue(), "application/pdf")},
                    data={"company": company_in, "doc_type": dtype, "year": int(year)},
                    timeout=900,
                )
            if r.ok:
                st.success(f"Indexed {r.json()['chunks']} chunks.")
            else:
                st.error(err_text(r))

# ---------------- Main ----------------
st.markdown(
    '<div class="hero"><div class="eyebrow">HYBRID RAG · PAGE-LEVEL CITATIONS</div>'
    "<h1>Due Diligence <span>Copilot</span></h1>"
    "<p>Turn company filings into risks, opportunities and answers, each tied to a source page.</p></div>",
    unsafe_allow_html=True,
)

if not api_ok:
    st.error("Cannot reach the API. Start it with: python -m uvicorn app.main:app --reload")

company = st.selectbox("Company", companies) if companies else st.text_input("Company (ingest documents first)")

tab_report, tab_qa = st.tabs(["REPORT", "ASK"])

with tab_report:
    if st.button("Generate report", type="primary") and company:
        with st.spinner("Analyzing documents..."):
            r = requests.get(f"{API}/report/{company}", timeout=300)
        if r.ok:
            st.session_state["report"] = {"company": company, "data": r.json()}
        else:
            st.session_state.pop("report", None)
            st.error(err_text(r))

    saved = st.session_state.get("report")
    if saved and saved["company"] == company:
        render_report(saved["data"])
    else:
        st.markdown('<div class="empty">Pick a company and generate a report.</div>', unsafe_allow_html=True)

with tab_qa:
    st.markdown('<div class="section-label">TRY ONE</div>', unsafe_allow_html=True)
    cols = st.columns(len(SUGGESTIONS))
    for col, s in zip(cols, SUGGESTIONS):
        col.button(
            s,
            key=f"sug-{s}",
            use_container_width=True,
            on_click=lambda t=s: st.session_state.update(q=t, ask_now=True),
        )

    q = st.text_input("Ask about the company", key="q", placeholder="e.g. What are the main supply chain risks?")
    asked = st.button("Ask", type="primary")
    if (asked or st.session_state.pop("ask_now", False)) and q and company:
        with st.spinner("Searching documents..."):
            r = requests.get(f"{API}/ask", params={"company": company, "q": q}, timeout=120)
        if r.ok:
            st.session_state["answer"] = {"q": q, "company": company, "data": r.json()}
        else:
            st.session_state.pop("answer", None)
            st.error(err_text(r))

    ans = st.session_state.get("answer")
    if ans and ans["company"] == company:
        st.markdown('<div class="section-label">ANSWER</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="answer">{esc(ans["data"]["answer"])}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chips">{chips(ans["data"]["sources"])}</div>', unsafe_allow_html=True)