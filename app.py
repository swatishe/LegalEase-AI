import streamlit as st
from utils.pdf_parser import extract_clauses_from_pdf
from utils.vector_store import build_vector_store, query_vector_store
from utils.llm import analyze_contract, chat_with_contract, compare_contracts
from components.ui import render_red_flags, render_checklist, render_summary

st.set_page_config(
    page_title="LegalEase AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-title { font-size: 2rem; font-weight: 700; color: #1a1a1a; }
    .subtitle   { color: #6b7280; font-size: 1rem; margin-top: -0.5rem; }
    .red-flag   { background: #fef2f2; border-left: 4px solid #ef4444;
                  padding: 0.75rem 1rem; border-radius: 0 8px 8px 0; margin: 0.5rem 0; }
    .green-ok   { background: #f0fdf4; border-left: 4px solid #22c55e;
                  padding: 0.75rem 1rem; border-radius: 0 8px 8px 0; margin: 0.5rem 0; }
    .warning    { background: #fffbeb; border-left: 4px solid #f59e0b;
                  padding: 0.75rem 1rem; border-radius: 0 8px 8px 0; margin: 0.5rem 0; }
    .clause-box { background: #f8fafc; border: 1px solid #e2e8f0;
                  border-radius: 8px; padding: 1rem; margin: 0.5rem 0;
                  font-size: 0.85rem; color: #374151; }
    .stButton > button { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for key in ["vector_store", "clauses", "analysis", "chat_history",
            "doc_name", "doc2_vector_store", "doc2_clauses", "doc2_name"]:
    if key not in st.session_state:
        st.session_state[key] = None
if "chat_history" not in st.session_state or st.session_state.chat_history is None:
    st.session_state.chat_history = []

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚖️ LegalEase AI")
    st.markdown("*Plain-English contract analysis powered by RAG*")
    st.divider()

    mode = st.radio(
        "Mode",
        ["📄 Analyze Contract", "💬 Chat with Contract", "🔀 Compare Two Contracts"],
        label_visibility="collapsed",
    )
    st.divider()
    st.markdown("**How it works**")
    st.markdown("""
1. Upload your contract PDF
2. AI chunks it by clause
3. RAG retrieves relevant sections
4. LLM explains in plain English
    """)
    st.divider()
    st.caption("Free stack: Groq · LangChain · FAISS · Streamlit")

# ── Main area ─────────────────────────────────────────────────────────────────
st.markdown('<p class="main-title">⚖️ LegalEase AI</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Upload any contract. Understand everything before you sign.</p>',
            unsafe_allow_html=True)
st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# MODE 1 — Analyze Contract
# ══════════════════════════════════════════════════════════════════════════════
if mode == "📄 Analyze Contract":
    uploaded = st.file_uploader("Upload contract PDF", type=["pdf"])

    if uploaded:
        if st.session_state.doc_name != uploaded.name:
            with st.spinner("Parsing clauses and building knowledge base..."):
                clauses = extract_clauses_from_pdf(uploaded)
                vs = build_vector_store(clauses)
                st.session_state.clauses = clauses
                st.session_state.vector_store = vs
                st.session_state.doc_name = uploaded.name
                st.session_state.analysis = None  # reset on new upload

        st.success(f"✅ Loaded **{uploaded.name}** — {len(st.session_state.clauses)} clauses extracted")

        contract_type = st.selectbox(
            "Contract type (helps tailor the analysis)",
            ["Auto-detect", "Employment", "NDA / Confidentiality", "Lease / Rental",
             "Freelance / Service", "SaaS / Terms of Service", "Other"],
        )

        if st.button("🔍 Analyze Contract", type="primary"):
            with st.spinner("Analyzing... this takes ~15 seconds"):
                st.session_state.analysis = analyze_contract(
                    st.session_state.clauses,
                    st.session_state.vector_store,
                    contract_type,
                )

        if st.session_state.analysis:
            a = st.session_state.analysis
            tab1, tab2, tab3 = st.tabs(["🚩 Red Flags", "📋 Summary", "✅ Before You Sign"])

            with tab1:
                render_red_flags(a.get("red_flags", []))

            with tab2:
                render_summary(a.get("summary", ""))

            with tab3:
                render_checklist(a.get("checklist", []))

# ══════════════════════════════════════════════════════════════════════════════
# MODE 2 — Chat with Contract
# ══════════════════════════════════════════════════════════════════════════════
elif mode == "💬 Chat with Contract":
    uploaded = st.file_uploader("Upload contract PDF to chat with", type=["pdf"])

    if uploaded:
        if st.session_state.doc_name != uploaded.name:
            with st.spinner("Building knowledge base..."):
                clauses = extract_clauses_from_pdf(uploaded)
                vs = build_vector_store(clauses)
                st.session_state.clauses = clauses
                st.session_state.vector_store = vs
                st.session_state.doc_name = uploaded.name
                st.session_state.chat_history = []

        st.success(f"✅ Ready to chat about **{uploaded.name}**")

        # Starter questions
        st.markdown("**Try asking:**")
        starter_cols = st.columns(3)
        starters = [
            "Can they terminate me without notice?",
            "What are my IP obligations?",
            "Are there any auto-renewal clauses?",
        ]
        for i, q in enumerate(starters):
            if starter_cols[i].button(q, use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": q})
                with st.spinner("Thinking..."):
                    answer, sources = chat_with_contract(
                        q, st.session_state.vector_store, st.session_state.chat_history
                    )
                st.session_state.chat_history.append({"role": "assistant", "content": answer, "sources": sources})

        # Chat display
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if msg["role"] == "assistant" and msg.get("sources"):
                    with st.expander("📎 Source clauses"):
                        for s in msg["sources"]:
                            st.markdown(f'<div class="clause-box">{s}</div>', unsafe_allow_html=True)

        # Input
        if prompt := st.chat_input("Ask anything about this contract..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Searching contract..."):
                    answer, sources = chat_with_contract(
                        prompt, st.session_state.vector_store, st.session_state.chat_history
                    )
                st.write(answer)
                if sources:
                    with st.expander("📎 Source clauses"):
                        for s in sources:
                            st.markdown(f'<div class="clause-box">{s}</div>', unsafe_allow_html=True)
            st.session_state.chat_history.append({"role": "assistant", "content": answer, "sources": sources})

# ══════════════════════════════════════════════════════════════════════════════
# MODE 3 — Compare Two Contracts
# ══════════════════════════════════════════════════════════════════════════════
else:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Contract A")
        up1 = st.file_uploader("Upload first contract", type=["pdf"], key="up1")
    with col2:
        st.markdown("### Contract B")
        up2 = st.file_uploader("Upload second contract", type=["pdf"], key="up2")

    if up1 and up2:
        if st.session_state.doc_name != up1.name:
            with st.spinner("Processing Contract A..."):
                c1 = extract_clauses_from_pdf(up1)
                st.session_state.clauses = c1
                st.session_state.vector_store = build_vector_store(c1)
                st.session_state.doc_name = up1.name

        if st.session_state.doc2_name != up2.name:
            with st.spinner("Processing Contract B..."):
                c2 = extract_clauses_from_pdf(up2)
                st.session_state.doc2_clauses = c2
                st.session_state.doc2_vector_store = build_vector_store(c2)
                st.session_state.doc2_name = up2.name

        st.success("Both contracts loaded. Ready to compare.")

        if st.button("🔀 Compare Contracts", type="primary"):
            with st.spinner("Comparing..."):
                comparison = compare_contracts(
                    st.session_state.clauses,
                    st.session_state.doc2_clauses,
                    up1.name,
                    up2.name,
                )

            st.markdown("### Comparison Results")
            categories = ["Termination", "Compensation", "IP / Ownership",
                          "Non-compete", "Liability", "Confidentiality"]
            for cat in categories:
                if cat in comparison:
                    with st.expander(f"**{cat}**"):
                        c = comparison[cat]
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.markdown(f"**{up1.name}**")
                            st.info(c.get("a", "Not found"))
                        with col_b:
                            st.markdown(f"**{up2.name}**")
                            st.info(c.get("b", "Not found"))
                        verdict = c.get("verdict", "")
                        if verdict:
                            st.markdown(f"**Verdict:** {verdict}")
