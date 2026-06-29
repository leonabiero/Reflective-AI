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
    page_title="Reflective Practice Companion",
    page_icon="🧠",
    layout="centered"
)

# -----------------------------
# CUSTOM CSS
# -----------------------------
st.markdown("""
<style>
    .stApp {
        background-color: #1A1A2E;
    }

    [data-testid="stSidebar"] {
        background-color: #16213E;
    }

    h1 {
        color: #AFA9EC;
        font-family: 'Georgia', serif;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-size: 1.1rem;
    }

    h2, h3 {
        color: #7F77DD;
        font-family: 'Georgia', serif;
    }

    p, div, label {
        color: #CECBF6;
        font-family: 'Helvetica Neue', sans-serif;
    }

    textarea {
        background-color: #26215C !important;
        border: 1px solid #534AB7 !important;
        border-radius: 8px !important;
        color: #EEEDFE !important;
    }

    .stButton > button {
        background-color: #7F77DD;
        color: white;
        border-radius: 8px;
        width: 100%;
    }

    .reflection-card {
        background-color: #26215C;
        border: 1px solid #534AB7;
        border-radius: 12px;
        padding: 1.2rem;
        color: #EEEDFE;
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
# LANGUAGE SYSTEM (FULL FIX)
# -----------------------------
LANGUAGES = {
    "English": {
        "title": "🧠 REFLECTIVE PRACTICE COMPANION",
        "paste": "Paste intervention report",
        "save": "💾 Save report",
        "daily": "🧠 Start Daily Reflection Session",
        "saved": "Saved successfully.",
        "empty": "Please enter a report.",
        "no_session": "No reports in today's session yet.",
        "reports_today": "Reports today:",
        "reflection_title": "🧠 Daily Reflection",
        "sidebar": "Today's Session",
        "lang_label": "Language",
        "generating": "Generating reflection..."
    },
    "Español": {
        "title": "🧠 ACOMPAÑANTE DE PRÁCTICA REFLEXIVA",
        "paste": "Pegar informe de intervención",
        "save": "💾 Guardar informe",
        "daily": "🧠 Iniciar sesión de reflexión diaria",
        "saved": "Guardado correctamente.",
        "empty": "Por favor introduce un informe.",
        "no_session": "No hay informes en la sesión de hoy.",
        "reports_today": "Informes de hoy:",
        "reflection_title": "🧠 Reflexión diaria",
        "sidebar": "Sesión de hoy",
        "lang_label": "Idioma",
        "generating": "Generando reflexión..."
    },
    "Euskara": {
        "title": "🧠 HAUSNARKETA LAGUNTZAILEA",
        "paste": "Itsatsi esku-hartze txostena",
        "save": "💾 Gorde txostena",
        "daily": "🧠 Eguneko hausnarketa hasi",
        "saved": "Ondo gorde da.",
        "empty": "Mesedez sartu txostena.",
        "no_session": "Ez dago txostenik gaurko saioan.",
        "reports_today": "Gaurko txostenak:",
        "reflection_title": "🧠 Eguneko hausnarketa",
        "sidebar": "Gaurko saioa",
        "lang_label": "Hizkuntza",
        "generating": "Hausnarketa sortzen..."
    }
}

lang = st.sidebar.selectbox("Language", list(LANGUAGES.keys()))
T = LANGUAGES[lang]

# -----------------------------
# HELPERS
# -----------------------------
def extract_client_name(text):
    match = re.search(r"client,\s*([A-Z][a-z]+\s[A-Z][a-z]+)", text)
    return match.group(1) if match else "Unknown"


def get_embedding(text):
    return model.encode(text).tolist()


def get_client_history(client_name):
    if client_name == "Unknown":
        return []

    try:
        return qdrant.search(
            collection_name="reflective_case_memory",
            query_vector=get_embedding(client_name),
            limit=3,
            with_payload=True
        )
    except:
        return []


# -----------------------------
# SESSION STATE
# -----------------------------
if "today_reports" not in st.session_state:
    st.session_state.today_reports = []

# -----------------------------
# HEADER
# -----------------------------
st.title(T["title"])
st.markdown("---")

# -----------------------------
# INPUT
# -----------------------------
report = st.text_area(T["paste"], height=250)

# -----------------------------
# SAVE REPORT
# -----------------------------
if st.button(T["save"]):

    if not report.strip():
        st.warning(T["empty"])
        st.stop()

    embedding = get_embedding(report)
    client_name = extract_client_name(report)

    payload = {
        "client_id": "auto",
        "client_name": client_name,
        "document_type": "Reflection",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "report_text": report
    }

    qdrant.upsert(
        collection_name="reflective_case_memory",
        points=[PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload=payload
        )]
    )

    st.session_state.today_reports.append({
        "text": report,
        "client_name": client_name,
        "embedding": embedding,
        "payload": payload
    })

    st.success(T["saved"])

# -----------------------------
# DAILY REFLECTION
# -----------------------------
st.markdown("---")

if st.button(T["daily"]):

    if len(st.session_state.today_reports) == 0:
        st.info(T["no_session"])
        st.stop()

    today = st.session_state.today_reports
    grouped = {}

    for r in today:
        grouped.setdefault(r["client_name"], []).append(r)

    memory_context = ""

    for client, reports in grouped.items():

        history = get_client_history(client)

        memory_context += f"\n\nCLIENT: {client}\n"
        memory_context += "\nTODAY:\n"

        for r in reports:
            memory_context += f"- {r['text']}\n"

        if history:
            memory_context += "\nHISTORY:\n"
            for h in history:
                p = h.payload
                memory_context += f"- {p.get('date')}: {p.get('report_text')}\n"
        else:
            memory_context += "\nHISTORY: First contact\n"

    system_prompt = """
You are a reflective practice assistant.

You do NOT evaluate or judge.

Structure your response:

1. Patterns Across Practice Today
2. Client Continuity & Change
3. Client Voice Analysis
4. Expanding Lens (bias/assumptions)
5. Evidence & Missing Information
6. Practice Reflection
7. Reflective Questions
"""

    with st.spinner(T["generating"]):

        response = claude.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=1200,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": memory_context
            }]
        )

    st.markdown("---")
    st.markdown(f"### {T['reflection_title']}")

    st.markdown(
        f'<div class="reflection-card">{response.content[0].text}</div>',
        unsafe_allow_html=True
    )

# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:
    st.markdown(f"### {T['sidebar']}")
    st.write(f"{T['reports_today']} {len(st.session_state.today_reports)}")
    st.markdown("---")
    st.caption("Reflective Practice Companion")
