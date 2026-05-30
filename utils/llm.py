"""
llm.py
All LLM interactions using Groq's free API.
Uses structured JSON prompting for reliable, parseable outputs.
@author: sshende
"""
import os
import json
import re
from groq import Groq
from utils.vector_store import query_vector_store, get_relevant_texts

# ── Groq client ────────────────────────────────────────────────────────────────
def _client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set. Add it to .streamlit/secrets.toml")
    return Groq(api_key=api_key)


def _chat(messages: list[dict], temperature: float = 0.1) -> str:
    """Raw Groq chat call. Low temperature for factual legal analysis."""
    response = _client().chat.completions.create(
        model="llama-3.3-70b-versatile",   # Groq free tier model
        messages=messages,
        temperature=temperature,
        max_tokens=2048,
    )
    return response.choices[0].message.content


def _parse_json(text: str) -> dict | list:
    """Strip markdown fences and parse JSON safely."""
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
    return json.loads(cleaned)


# ── Red flag topics to probe with RAG ─────────────────────────────────────────
RED_FLAG_QUERIES = [
    "termination without cause or notice",
    "non-compete non-solicitation restrictions",
    "intellectual property ownership assignment",
    "automatic renewal evergreen clause",
    "liability limitation indemnification",
    "arbitration dispute resolution waiver",
    "confidentiality obligations duration",
    "unilateral modification changes to terms",
    "governing law jurisdiction",
    "payment penalties late fees",
]


def analyze_contract(
    clauses: list[dict],
    vector_store,
    contract_type: str = "Auto-detect",
) -> dict:
    """
    Full contract analysis: red flags, summary, and before-you-sign checklist.
    Uses RAG to retrieve relevant clauses per topic.
    """
    # Step 1: Gather relevant excerpts via RAG for each red-flag topic
    retrieved_sections = {}
    for query in RED_FLAG_QUERIES:
        docs = query_vector_store(vector_store, query, k=2)
        if docs:
            retrieved_sections[query] = [d.page_content[:600] for d in docs]

    context = "\n\n---\n\n".join(
        f"TOPIC: {topic}\n" + "\n".join(texts)
        for topic, texts in retrieved_sections.items()
    )

    # Step 2: Full clause list for summary context (truncated)
    all_text = "\n\n".join(c["text"][:300] for c in clauses[:30])

    # Step 3: LLM analysis
    system = """You are a contract analysis assistant. You help non-lawyers understand
legal documents in plain English. You are thorough, accurate, and always flag
potential risks clearly. You never give formal legal advice — you explain what
clauses mean and what questions to ask a lawyer.
Respond ONLY with valid JSON, no preamble, no markdown."""

    user = f"""Analyze this contract (type: {contract_type}).

RETRIEVED CLAUSES BY TOPIC:
{context}

FULL CONTRACT OVERVIEW:
{all_text}

Return a JSON object with exactly these keys:
{{
  "red_flags": [
    {{
      "title": "Short title",
      "severity": "high|medium|low",
      "clause_excerpt": "The exact problematic text (max 150 chars)",
      "plain_english": "What this means in plain English",
      "what_to_ask": "A specific question to ask a lawyer or the other party"
    }}
  ],
  "summary": "A 3-4 sentence plain-English overview of what this contract is and what it obligates each party to do.",
  "checklist": [
    {{
      "item": "Action or question",
      "category": "Negotiate|Clarify|Verify|Lawyer"
    }}
  ],
  "contract_type_detected": "e.g. Employment Agreement"
}}

Include 4-8 red flags (only real ones — don't invent issues) and 6-10 checklist items."""

    raw = _chat([{"role": "system", "content": system},
                 {"role": "user", "content": user}])
    try:
        return _parse_json(raw)
    except Exception:
        return {
            "red_flags": [],
            "summary": raw,
            "checklist": [],
            "contract_type_detected": contract_type,
        }


def chat_with_contract(
    question: str,
    vector_store,
    history: list[dict],
) -> tuple[str, list[str]]:
    """
    RAG-powered chat: retrieve relevant clauses, then answer.
    Returns (answer_text, source_clauses).
    """
    # Retrieve relevant clauses
    docs = query_vector_store(vector_store, question, k=4)
    source_texts = [d.page_content for d in docs]
    context = "\n\n---\n\n".join(t[:800] for t in source_texts)

    system = """You are a contract assistant helping someone understand their contract.
Always base your answer on the provided contract clauses.
If the answer isn't in the provided clauses, say so clearly.
Be concise, plain-English, and helpful. Never give formal legal advice."""

    # Build message history (last 6 turns to stay within context)
    messages = [{"role": "system", "content": system}]
    for msg in history[-6:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({
        "role": "user",
        "content": f"""RELEVANT CONTRACT CLAUSES:
{context}

QUESTION: {question}

Answer based on these clauses. Quote the relevant text briefly if helpful."""
    })

    answer = _chat(messages, temperature=0.2)
    return answer, source_texts


def compare_contracts(
    clauses_a: list[dict],
    clauses_b: list[dict],
    name_a: str,
    name_b: str,
) -> dict:
    """
    Compare two contracts across key categories.
    Uses a combined context of both contracts.
    """
    categories = ["Termination", "Compensation", "IP / Ownership",
                  "Non-compete", "Liability", "Confidentiality"]

    text_a = "\n".join(c["text"][:250] for c in clauses_a[:20])
    text_b = "\n".join(c["text"][:250] for c in clauses_b[:20])

    system = """You are a contract comparison expert. Compare two contracts
and explain differences in plain English. Respond ONLY with valid JSON."""

    user = f"""Compare these two contracts on the listed categories.

CONTRACT A ({name_a}):
{text_a}

CONTRACT B ({name_b}):
{text_b}

For each category return a JSON object:
{{
  "Termination": {{
    "a": "What contract A says in 1-2 sentences",
    "b": "What contract B says in 1-2 sentences",
    "verdict": "Which is better for the signer and why (1 sentence)"
  }},
  "Compensation": {{ ... }},
  "IP / Ownership": {{ ... }},
  "Non-compete": {{ ... }},
  "Liability": {{ ... }},
  "Confidentiality": {{ ... }}
}}"""

    raw = _chat([{"role": "system", "content": system},
                 {"role": "user", "content": user}])
    try:
        return _parse_json(raw)
    except Exception:
        return {}
