import os

import requests
import streamlit as st

API = os.getenv("API_URL", "http://localhost:8000")
SEV = {"high": "🔴", "medium": "🟠", "low": "🟢"}


def err_text(r) -> str:
    """Safely get an error message even when the response is not JSON."""
    try:
        return str(r.json().get("detail", r.text))
    except Exception:
        return r.text or f"HTTP {r.status_code}"


st.set_page_config(page_title="AI Due Diligence Copilot", layout="wide")
st.title("AI Due Diligence Copilot")
st.caption("Source-backed risk assessments, growth opportunities and executive summaries from company documents.")

with st.sidebar:
    st.header("Add documents")
    f = st.file_uploader("Filing / statement / deck / market report (PDF)", type="pdf")
    company_in = st.text_input("Company name")
    dtype = st.selectbox("Document type", ["10-K", "10-Q", "Annual Report", "Financial Statement", "Investor Deck", "Market Report"])
    year = st.number_input("Year", 2000, 2030, 2024)
    if st.button("Ingest", use_container_width=True):
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

try:
    companies = requests.get(f"{API}/companies", timeout=30).json()
except Exception:
    companies = []
    st.error("Cannot reach the API. Start it with: python -m uvicorn app.main:app --reload")

company = st.selectbox("Company", companies) if companies else st.text_input("Company (ingest documents first)")

tab_report, tab_qa = st.tabs(["Due Diligence Report", "Ask a Question"])

with tab_report:
    if st.button("Generate report", type="primary") and company:
        with st.spinner("Analyzing documents..."):
            r = requests.get(f"{API}/report/{company}", timeout=300)
        if not r.ok:
            st.error(err_text(r))
        else:
            rep = r.json()
            st.subheader("Executive Summary")
            st.write(rep["executive_summary"])
            col1, col2 = st.columns(2)
            for col, title, key in [(col1, "Risks", "risks"), (col2, "Growth Opportunities", "growth_opportunities")]:
                with col:
                    st.subheader(title)
                    if not rep[key]:
                        st.info("No well-supported findings.")
                    for x in rep[key]:
                        icon = SEV.get(x["severity"].lower(), "⚪")
                        with st.expander(f"{icon} {x['title']} ({x['severity']})"):
                            st.write(x["explanation"])
                            st.caption("Sources: " + " • ".join(x["sources"]))

with tab_qa:
    q = st.text_input("Ask about the company (e.g. What are the main supply chain risks?)")
    if st.button("Ask") and q and company:
        with st.spinner("Searching documents..."):
            r = requests.get(f"{API}/ask", params={"company": company, "q": q}, timeout=120)
        if r.ok:
            st.write(r.json()["answer"])
            st.caption("Sources: " + " • ".join(r.json()["sources"]))
        else:
            st.error(err_text(r))