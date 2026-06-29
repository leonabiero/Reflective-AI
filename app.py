import streamlit as st
from anthropic import Anthropic
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from qdrant_client.models import PointStruct
import re
import uuid
from datetime import datetime

# -----------------------------
# CONFIG
# -----------------------------
QDRANT_URL = st.secrets["QDRANT_URL"]
QDRANT_API_KEY = st.secrets["QDRANT_API_KEY"]
ANTHROPIC_API_KEY = st.secrets["ANTHROPIC_API_KEY"]

# -----------------------------
# CLIENTS
# -----------------------------
claude = Anthropic(api_key=ANTHROPIC_API_KEY)

qdrant = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)

model = SentenceTransformer("all-MiniLM-L6-v2")

# -----------------------------
# LANGUAGE SYSTEM
# -----------------------------
LANGUAGES = {
    "Español": {
        "title": "🧠 Asistente de Práctica Reflexiva",
        "paste": "Pega el informe aquí",
        "mode": "Modo de reflexión",
        "single": "Caso individual",
        "cross": "Casos múltiples",
        "reflect": "Reflexionar",
        "save": "Guardar",
        "summary": "Resumen",
        "memory": "Memoria",
        "risk": "Riesgo",
    },
    "Euskara": {
        "title": "🧠 Hausnarketa Laguntzailea",
        "paste": "Itsatsi txostena",
        "mode": "Hausnarketa modua",
        "single": "Kasu bakarra",
        "cross": "Kasu anitz",
        "reflect": "Hausnartu",
        "save": "Gorde",
        "summary": "Laburpena",
        "memory": "Memoria",
        "risk": "Arriskua",
    },
    "English": {
        "title": "🧠 Reflective Practice Assistant",
        "paste": "Paste report here",
        "mode": "Reflection Mode",
        "single": "Single case",
        "cross": "Multiple cases",
        "reflect": "Reflect",
        "save": "Save",
        "summary": "Summary",
        "memory": "Memory",
        "risk": "Risk",
    }
}

lang = st.sidebar.selectbox("Language", list(LANGUAGES.keys()), index=0)
T = LANGUAGES[lang]

# -----------------------------
# HELPERS
# -----------------------------
def extract_client_name(text):
    match = re.search(r"client,\s*([A-Z][a-z]+\s[A-Z][a-z]+)", text)
    return match.group(1) if match else None


def get_embedding(text):
    return model.encode(text).tolist()


def calculate_risk(text):
    text = text.lower()
    score = 0

    for w in ["homeless", "evicted", "violence", "abuse", "unsafe", "no income"]:
        if w in text:
            score += 2

    for w in ["unstable", "jobless", "stress", "struggling"]:
        if w in text:
            score += 1

    if score >= 4:
        return "🔴 High Risk"
    elif score >= 2:
        return "🟠 Medium Risk"
    return "🟢 Low Risk"


# -----------------------------
# STATE
# -----------------------------
for k in ["last_report", "last_embedding", "last_client", "last_results"]:
    if k not in st.session_state:
        st.session_state[k] = None if k != "last_results" else []

# -----------------------------
# UI
# -----------------------------
st.title(T["title"])

pitch_mode = st.toggle("🎯 Pitch Mode (Clean UI)", value=True)

report = st.text_area(T["paste"], height=250)

mode = st.radio(T["mode"], [T["single"], T["cross"]])

# -----------------------------
# REFLECT
# -----------------------------
if st.button(T["reflect"]):

    if not report.strip():
        st.warning("Enter report")
        st.stop()

    query_vector = get_embedding(report)
    client_name = extract_client_name(report)

    st.session_state.last_report = report
    st.session_state.last_embedding = query_vector
    st.session_state.last_client = client_name

    query_filter = None
    if mode == T["single"] and client_name:
        query_filter = {
            "must": [{"key": "client_name", "match": {"value": client_name}}]
        }

    results = qdrant.query_points(
        collection_name="reflective_case_memory",
        query=query_vector,
        query_filter=query_filter,
        limit=5,
        with_payload=True
    ).points

    st.session_state.last_results = results

    # ---------------- SUMMARY ----------------
    st.info(f"""
**{T['summary']}**

Client: {client_name or "Not detected"}

Cases found: {len(results)}
""")

    # ---------------- RISK ----------------
    st.info(f"{T['risk']}: {calculate_risk(report)}")

    # ---------------- MEMORY ----------------
    st.subheader("🔍 Memory & Similarity")

    memory_text = ""

    if results:
        for i, r in enumerate(results):
            st.write(f"Case {i+1} similarity: {round(r.score, 3)}")

            p = r.payload
            memory_text += f"""
CASE {i+1}
Client: {p.get('client_name')}
Type: {p.get('document_type')}
Date: {p.get('date')}
Report: {p.get('report_text')}
"""
    else:
        st.info("No historical matches found.")
        memory_text = "No previous cases."

    # ---------------- CLAUDE ----------------
    response = claude.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=1200,
        system=f"""
You are a reflective assistant.

Respond in {lang}.

Never judge.

1. Observation vs Interpretation
2. Evidence Strength
3. Missing Information
4. Alternatives
5. Client Voice
6. Reflection
""",
        messages=[{
            "role": "user",
            "content": f"REPORT:\n{report}\n\nHISTORY:\n{memory_text}"
        }]
    )

    st.subheader("🧠 AI Reflection")
    st.write(response.content[0].text)

# -----------------------------
# FINAL REVIEW STEP
# -----------------------------
st.divider()
st.subheader("🧾 Final Review")

if st.session_state.last_report:

    review = st.radio(
        "Final decision",
        ["Submit without changes", "Edit before saving"]
    )

    final_report = st.session_state.last_report

    if review == "Edit before saving":
        final_report = st.text_area(
            "Edit report",
            value=st.session_state.last_report,
            height=200
        )

    if st.button(T["save"]):

        qdrant.upsert(
            collection_name="reflective_case_memory",
            points=[PointStruct(
                id=str(uuid.uuid4()),
                vector=st.session_state.last_embedding,
                payload={
                    "client_id": "auto",
                    "client_name": st.session_state.last_client or "unknown",
                    "document_type": "Reflection",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "report_text": final_report,
                    "original_report": st.session_state.last_report,
                    "review_mode": review
                }
            )]
        )

        st.success("Saved successfully!")

# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:
    st.subheader(T["memory"])

    if st.session_state.last_results:
        for r in st.session_state.last_results:
            p = r.payload
            st.markdown(f"""
**Client:** {p.get('client_name')}  
**Type:** {p.get('document_type')}  
**Date:** {p.get('date')}  
---
""")
    else:
        st.info("No memory loaded")
