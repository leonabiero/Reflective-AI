import streamlit as st
from anthropic import Anthropic
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from qdrant_client.models import PointStruct
import re
import uuid
from datetime import datetime

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Reflective Practice Assistant",
    page_icon="🧠",
    layout="centered"
)

# -----------------------------
# CUSTOM CSS
# -----------------------------
st.markdown("""
<style>
    /* Background */
    .stApp {
        background-color: #FDF6F0;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #F2E8DF;
    }

    /* Main title */
    h1 {
        color: #5C3D2E;
        font-family: 'Georgia', serif;
        font-size: 2rem;
        padding-bottom: 0.2rem;
    }

    /* Subheaders */
    h2, h3 {
        color: #7A4F3A;
        font-family: 'Georgia', serif;
    }

    /* Paragraph text */
    p, div, label {
        color: #3D2B1F;
        font-family: 'Helvetica Neue', sans-serif;
    }

    /* Text area */
    textarea {
        background-color: #FFFAF6 !important;
        border: 1.5px solid #D4A98A !important;
        border-radius: 10px !important;
        color: #3D2B1F !important;
        font-size: 0.95rem !important;
    }

    /* Primary button */
    .stButton > button {
        background-color: #C17D5A;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-size: 1rem;
        font-weight: 600;
        transition: background-color 0.2s ease;
    }

    .stButton > button:hover {
        background-color: #A0623F;
        color: white;
    }

    /* Info boxes */
    [data-testid="stAlert"] {
        background-color: #F5E6D8;
        border-left: 4px solid #C17D5A;
        border-radius: 8px;
        color: #3D2B1F;
    }

    /* Success box */
    .stSuccess {
        background-color: #E8F5E9 !important;
        border-left: 4px solid #7BAE7F !important;
        border-radius: 8px !important;
    }

    /* Divider */
    hr {
        border-color: #D4A98A;
    }

    /* Radio buttons */
    .stRadio label {
        color: #5C3D2E !important;
        font-weight: 500;
    }

    /* Select box */
    .stSelectbox label {
        color: #5C3D2E !important;
        font-weight: 600;
    }

    /* Toggle */
    .stToggle label {
        color: #5C3D2E !important;
    }

    /* Caption */
    .stCaption {
        color: #9C7B6B !important;
        font-style: italic;
    }

    /* Sidebar text */
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] div {
        color: #5C3D2E;
    }

    /* Card-style container */
    .reflection-card {
        background-color: #FFFAF6;
        border: 1px solid #D4A98A;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

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
        "subtitle": "Apoyo a la reflexión profesional en trabajo social",
        "paste": "Pega el informe aquí",
        "mode": "Modo de reflexión",
        "single": "Caso individual",
        "cross": "Casos múltiples",
        "reflect": "Reflexionar",
        "save": "Guardar en memoria",
        "summary": "Resumen",
        "memory": "Casos similares",
        "risk": "Nivel de atención",
    },
    "Euskara": {
        "title": "🧠 Hausnarketa Laguntzailea",
        "subtitle": "Gizarte laneko hausnarketa profesionalerako laguntza",
        "paste": "Itsatsi txostena hemen",
        "mode": "Hausnarketa modua",
        "single": "Kasu bakarra",
        "cross": "Kasu anitz",
        "reflect": "Hausnartu",
        "save": "Memorian gorde",
        "summary": "Laburpena",
        "memory": "Antzeko kasuak",
        "risk": "Arreta maila",
    },
    "English": {
        "title": "🧠 Reflective Practice Assistant",
        "subtitle": "Supporting professional reflection in social work",
        "paste": "Paste the intervention report here",
        "mode": "Reflection Mode",
        "single": "Single case",
        "cross": "Multiple cases",
        "reflect": "Reflect",
        "save": "Save to memory",
        "summary": "Summary",
        "memory": "Similar cases",
        "risk": "Attention level",
    }
}

lang = st.sidebar.selectbox("🌐 Language / Idioma / Hizkuntza", list(LANGUAGES.keys()), index=0)
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
        return "🔴 High attention needed"
    elif score >= 2:
        return "🟠 Moderate attention"
    return "🟢 Stable situation"


# -----------------------------
# STATE
# -----------------------------
for k in ["last_report", "last_embedding", "last_client", "last_results"]:
    if k not in st.session_state:
        st.session_state[k] = None if k != "last_results" else []

# -----------------------------
# HEADER
# -----------------------------
st.title(T["title"])
st.caption(T["subtitle"])
st.markdown("---")

# -----------------------------
# REPORT INPUT
# -----------------------------
st.markdown("### 📝 Intervention Report")
report = st.text_area(T["paste"], height=250, placeholder="Write or paste the professional intervention text here...")

mode = st.radio(T["mode"], [T["single"], T["cross"]], horizontal=True)

st.markdown("")

# -----------------------------
# REFLECT
# -----------------------------
if st.button(f"🔍 {T['reflect']}", use_container_width=True):

    if not report.strip():
        st.warning("Please enter a report before reflecting.")
        st.stop()

    with st.spinner("Analysing the report..."):

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
    st.markdown("---")
    st.markdown("### 📊 Summary")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Client", client_name or "Not detected")
    with col2:
        st.metric("Similar cases found", len(results))
    with col3:
        st.metric(T["risk"], calculate_risk(report))

    # ---------------- MEMORY ----------------
    if results:
        st.markdown("### 🗂️ Similar Past Cases")
        for i, r in enumerate(results):
            p = r.payload
            with st.expander(f"Case {i+1} — similarity: {round(r.score, 3)}"):
                st.write(f"**Client:** {p.get('client_name', 'Unknown')}")
                st.write(f"**Type:** {p.get('document_type', '—')}")
                st.write(f"**Date:** {p.get('date', '—')}")
    else:
        st.info("No similar past cases found — this appears to be a new pattern.")

    # ---------------- CLAUDE ----------------
    memory_text = ""
    if results:
        for i, r in enumerate(results):
            p = r.payload
            memory_text += f"""
CASE {i+1}
Client: {p.get('client_name')}
Type: {p.get('document_type')}
Date: {p.get('date')}
Report: {p.get('report_text')}
"""
    else:
        memory_text = "No previous cases."

    with st.spinner("Generating reflective questions..."):
        response = claude.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=1200,
            system=f"""
You are a warm, thoughtful Reflective Practice Assistant supporting social work professionals.

Respond in {lang}.

Never judge the professional or the report. Your role is to open up thinking, not evaluate quality.

Structure your response around these six areas:
1. Observation vs Interpretation — what is fact, what is assumption?
2. Evidence Strength — what supports the conclusions drawn?
3. Missing Information — what is absent that might matter?
4. Alternative Explanations — what other perspectives could exist?
5. Client Voice — how present is the person's own voice and goals?
6. Practice Reflection — what might this reveal about professional practice patterns?

Use gentle, curious, open-ended questions throughout.
""",
            messages=[{
                "role": "user",
                "content": f"REPORT:\n{report}\n\nHISTORY:\n{memory_text}"
            }]
        )

    st.markdown("---")
    st.markdown("### 🧠 Reflective Questions")
    st.markdown(
        f'<div class="reflection-card">{response.content[0].text}</div>',
        unsafe_allow_html=True
    )

# -----------------------------
# FINAL REVIEW & SAVE
# -----------------------------
if st.session_state.last_report:
    st.markdown("---")
    st.markdown("### 🧾 Review & Save")

    review = st.radio(
        "Would you like to edit the report before saving?",
        ["Save as is", "Edit before saving"]
    )

    final_report = st.session_state.last_report

    if review == "Edit before saving":
        final_report = st.text_area(
            "Edit the report below:",
            value=st.session_state.last_report,
            height=200
        )

    if st.button(f"💾 {T['save']}", use_container_width=True):
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
        st.success("✅ Saved to memory successfully!")

# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:
    st.markdown("---")
    st.subheader(f"🗂️ {T['memory']}")

    if st.session_state.last_results:
        for r in st.session_state.last_results:
            p = r.payload
            st.markdown(f"""
**Client:** {p.get('client_name', '—')}
**Type:** {p.get('document_type', '—')}
**Date:** {p.get('date', '—')}

---
""")
    else:
        st.info("No cases loaded yet. Run a reflection to see similar cases here.")

    st.markdown("---")
    st.caption("Reflective Practice Assistant · EDE Fundazioa · BGT 2026")
