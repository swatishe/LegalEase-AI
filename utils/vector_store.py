"""
vector_store.py
Builds a FAISS vector store from contract clauses using
HuggingFace sentence-transformers (100% free, runs locally).
@author: sshende
"""
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

# Free, lightweight embedding model — no API key required
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_embeddings = None  # lazy-loaded singleton


def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=EMBED_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings


def build_vector_store(clauses: list[dict]) -> FAISS:
    """
    Build a FAISS index from clause dicts.
    Stores clause title + index as metadata for source display.
    """
    docs = [
        Document(
            page_content=c["text"],
            metadata={"title": c.get("title", f"Clause {c['index']}"), "index": c["index"]},
        )
        for c in clauses
    ]
    embeddings = _get_embeddings()
    vector_store = FAISS.from_documents(docs, embeddings)
    return vector_store


def query_vector_store(
    vector_store: FAISS,
    query: str,
    k: int = 4,
) -> list[Document]:
    """Retrieve top-k most relevant clauses for a query."""
    return vector_store.similarity_search(query, k=k)


def get_relevant_texts(vector_store: FAISS, query: str, k: int = 4) -> list[str]:
    """Convenience: return just the text strings."""
    docs = query_vector_store(vector_store, query, k=k)
    return [d.page_content for d in docs]
