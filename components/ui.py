"""
ui.py
Streamlit rendering components for analysis results.
"""
import streamlit as st

SEVERITY_CONFIG = {
    "high":   {"emoji": "🔴", "label": "High Risk",   "css": "red-flag"},
    "medium": {"emoji": "🟡", "label": "Medium Risk",  "css": "warning"},
    "low":    {"emoji": "🟢", "label": "Low Risk",     "css": "green-ok"},
}

CATEGORY_ICONS = {
    "Negotiate": "🤝",
    "Clarify":   "❓",
    "Verify":    "✅",
    "Lawyer":    "⚖️",
}


def render_red_flags(red_flags: list[dict]):
    if not red_flags:
        st.info("No significant red flags detected. Always review with a lawyer for important contracts.")
        return

    high   = [f for f in red_flags if f.get("severity") == "high"]
    medium = [f for f in red_flags if f.get("severity") == "medium"]
    low    = [f for f in red_flags if f.get("severity") == "low"]

    # Summary counts
    c1, c2, c3 = st.columns(3)
    c1.metric("🔴 High Risk", len(high))
    c2.metric("🟡 Medium Risk", len(medium))
    c3.metric("🟢 Low Risk", len(low))
    st.divider()

    for flag in red_flags:
        sev = flag.get("severity", "low")
        cfg = SEVERITY_CONFIG.get(sev, SEVERITY_CONFIG["low"])

        with st.expander(f"{cfg['emoji']} {flag.get('title', 'Unnamed clause')} — {cfg['label']}"):
            if flag.get("clause_excerpt"):
                st.markdown(
                    f'<div class="clause-box">📄 <em>{flag["clause_excerpt"]}</em></div>',
                    unsafe_allow_html=True,
                )
            st.markdown(f"**What this means:** {flag.get('plain_english', '')}")
            if flag.get("what_to_ask"):
                st.markdown(
                    f'<div class="{cfg["css"]}">💬 <strong>Ask:</strong> {flag["what_to_ask"]}</div>',
                    unsafe_allow_html=True,
                )


def render_summary(summary: str):
    if not summary:
        st.warning("Summary not available.")
        return

    st.markdown("### What this contract says")
    st.markdown(summary)
    st.divider()
    st.caption("⚠️ This is an AI-generated summary for informational purposes only. "
               "It is not legal advice. Consult a qualified attorney before signing.")


def render_checklist(checklist: list[dict]):
    if not checklist:
        st.info("No checklist items generated.")
        return

    st.markdown("### Before you sign, make sure to:")

    grouped: dict[str, list] = {}
    for item in checklist:
        cat = item.get("category", "Verify")
        grouped.setdefault(cat, []).append(item.get("item", ""))

    for cat, items in grouped.items():
        icon = CATEGORY_ICONS.get(cat, "•")
        st.markdown(f"**{icon} {cat}**")
        for item in items:
            st.checkbox(item, key=f"check_{item[:40]}")
        st.markdown("")
