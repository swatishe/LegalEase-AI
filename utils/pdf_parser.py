"""
pdf_parser.py
Extracts and chunks contract text by clause boundaries,
not by arbitrary token count — the key RAG design choice in LegalEase.
@author: sshende
"""
import re
import io
import fitz  # PyMuPDF


# ── Clause boundary patterns ───────────────────────────────────────────────────
CLAUSE_PATTERNS = [
    # Numbered: "1.", "1.1", "1.1.1"
    r"^\s*\d+(\.\d+)*\.?\s+[A-Z]",
    # Lettered: "A.", "(a)", "(A)"
    r"^\s*(\(?\s*[A-Za-z]\s*[\.\)])\s+",
    # ALL CAPS headings: "TERMINATION", "CONFIDENTIALITY"
    r"^\s*[A-Z][A-Z\s]{3,}[A-Z]\s*$",
    # Title Case headings: "Governing Law", "Dispute Resolution"
    r"^\s*([A-Z][a-z]+\s){1,4}[A-Z][a-z]+\s*$",
    # "Section 3", "Article IV", "Clause 2"
    r"^\s*(Section|Article|Clause|Part)\s+[\dIVXivx]+",
]
CLAUSE_RE = re.compile("|".join(CLAUSE_PATTERNS), re.MULTILINE)


def extract_text_from_pdf(file_obj) -> str:
    """Extract raw text from a PDF file object."""
    data = file_obj.read() if hasattr(file_obj, "read") else file_obj
    doc = fitz.open(stream=data, filetype="pdf")
    pages = []
    for page in doc:
        pages.append(page.get_text("text"))
    doc.close()
    return "\n".join(pages)


def split_into_clauses(text: str, min_length: int = 80) -> list[dict]:
    """
    Split contract text into clause chunks using boundary detection.
    Returns list of dicts: {title, text, index}
    """
    # Find all clause-start positions
    boundaries = [m.start() for m in CLAUSE_RE.finditer(text)]

    if len(boundaries) < 3:
        # Fallback: paragraph-based chunking
        return _paragraph_chunks(text, min_length)

    clauses = []
    for i, start in enumerate(boundaries):
        end = boundaries[i + 1] if i + 1 < len(boundaries) else len(text)
        chunk = text[start:end].strip()

        if len(chunk) < min_length:
            continue

        # Extract heading (first line) from body
        lines = chunk.splitlines()
        title = lines[0].strip()[:120]
        body = " ".join(lines[1:]).strip() if len(lines) > 1 else chunk

        clauses.append({
            "index": len(clauses),
            "title": title,
            "text": chunk,
            "body": body,
        })

    return clauses


def _paragraph_chunks(text: str, min_length: int = 80) -> list[dict]:
    """Fallback: split by double newlines (paragraphs)."""
    paragraphs = re.split(r"\n\s*\n", text)
    clauses = []
    for i, para in enumerate(paragraphs):
        para = para.strip()
        if len(para) < min_length:
            continue
        lines = para.splitlines()
        clauses.append({
            "index": i,
            "title": lines[0].strip()[:120],
            "text": para,
            "body": para,
        })
    return clauses


def extract_clauses_from_pdf(file_obj) -> list[dict]:
    """
    Main entry point.
    Returns list of clause dicts ready to be embedded.
    """
    raw_text = extract_text_from_pdf(file_obj)

    # Light cleanup
    raw_text = re.sub(r"\n{3,}", "\n\n", raw_text)
    raw_text = re.sub(r"[ \t]{2,}", " ", raw_text)
    raw_text = re.sub(r"-\n(\w)", r"\1", raw_text)  # dehyphenate line breaks

    clauses = split_into_clauses(raw_text)
    return clauses


def clauses_to_texts(clauses: list[dict]) -> list[str]:
    """Extract just the text content for embedding."""
    return [c["text"] for c in clauses]
