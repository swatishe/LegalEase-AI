# ⚖️ LegalEase AI

> **Upload any contract. Understand everything before you sign.**

[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-FF4B4B?logo=streamlit)](https://streamlit.io)
[![Groq](https://img.shields.io/badge/LLM-Groq%20(Free)-00A67E)](https://console.groq.com)
[![FAISS](https://img.shields.io/badge/Vector%20Store-FAISS-blue)](https://github.com/facebookresearch/faiss)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

LegalEase AI is a **RAG-powered contract analyzer** that helps non-lawyers understand dense legal documents — employment contracts, NDAs, lease agreements, SaaS terms — in plain English. Built entirely on free services.

---

## 🎯 The Problem

People sign contracts they don't understand. A lawyer costs $300/hr. LegalEase costs $0.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🚩 **Red Flag Detection** | Highlights risky clauses (non-competes, auto-renewal, liability waivers) with severity ratings |
| 📋 **Plain-English Summary** | 3-4 sentence overview of what the contract actually says |
| ✅ **Before-You-Sign Checklist** | Actionable items — what to negotiate, clarify, or ask a lawyer |
| 💬 **Chat Mode** | Ask plain-English questions: *"Can they fire me without notice?"* |
| 🔀 **Contract Comparison** | Side-by-side comparison of two contracts (e.g., two job offers) |
| 📎 **Source Citations** | Every answer links back to the exact clause it came from |

---

## 🏗️ Architecture

```
PDF Upload
    │
    ▼
┌─────────────────────────────┐
│  Clause-Aware PDF Parser    │  ← Chunks by clause boundary, not token count
│  (PyMuPDF + regex)          │
└─────────────┬───────────────┘
              │ list of clause dicts
              ▼
┌─────────────────────────────┐
│  Embedding + FAISS Index    │  ← sentence-transformers/all-MiniLM-L6-v2 (free, local)
│  (LangChain + FAISS)        │
└─────────────┬───────────────┘
              │ similarity search
              ▼
┌─────────────────────────────┐
│  RAG Retrieval              │  ← Top-k relevant clauses per query
└─────────────┬───────────────┘
              │ context + query
              ▼
┌─────────────────────────────┐
│  Groq LLM (llama-3.3-70b)  │  ← Structured JSON output (red flags, summary, checklist)
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Streamlit UI               │  ← Tabs, chat interface, comparison view
└─────────────────────────────┘
```

**Key design decision:** Chunking by clause boundary (numbered sections, ALL CAPS headings, "Section X") instead of arbitrary token windows preserves legal meaning. A clause split mid-sentence loses context; a clause chunked as a unit retains it.

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/legalease-ai.git
cd legalease-ai
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Get a free Groq API key
Sign up at [console.groq.com](https://console.groq.com) — it's free with generous limits.

### 4. Add your API key
```toml
# .streamlit/secrets.toml
GROQ_API_KEY = "gsk_your_key_here"
```

### 5. Run
```bash
streamlit run app.py
```

---

## ☁️ Deploy Free (Streamlit Cloud)

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo → select `app.py`
4. Add `GROQ_API_KEY` under **Secrets**
5. Deploy — you get a public URL instantly

---

## 🧰 Tech Stack

| Layer | Tool | Cost |
|---|---|---|
| UI | Streamlit | Free |
| LLM | Groq (llama-3.3-70b) | Free tier |
| Embeddings | sentence-transformers (local) | Free |
| Vector Store | FAISS (in-memory) | Free |
| PDF Parsing | PyMuPDF | Free |
| Deployment | Streamlit Cloud | Free |

**Total infrastructure cost: $0/month**

---

## 📁 Project Structure

```
legalease-ai/
├── app.py                    # Main Streamlit app (3 modes)
├── requirements.txt
├── .streamlit/
│   ├── config.toml           # Theme config
│   └── secrets.toml          # API keys (gitignored)
├── utils/
│   ├── pdf_parser.py         # Clause-aware PDF chunker
│   ├── vector_store.py       # FAISS index builder + retriever
│   └── llm.py                # All Groq API calls
└── components/
    └── ui.py                 # Streamlit rendering components
```

---

## ⚠️ Disclaimer

LegalEase AI is for informational purposes only. It is not a substitute for professional legal advice. Always consult a qualified attorney before signing important contracts.

---

## 📄 License

MIT — free to use, modify, and deploy.
