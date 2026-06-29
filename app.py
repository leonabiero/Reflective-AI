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
    .stApp {
        background-color: #1A1A2E;
    }

    [data-testid="stSidebar"] {
        background-color: #16213E;
    }

    h1 {
        color: #AFA9EC;
        font-family: 'Georgia', serif;
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
# LANGUAGE (kept minimal but intact)
# -----------------------------
LANGUAGES = {
    "English": {
        "title": "🧠 REFLECTIVE PRACTICE COMPANION",
        "paste": "Paste intervention report",
        "save": "Save report",
        "daily": "Start Daily Reflection Session"
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
        results = qdrant.search(
            collection_name="reflective_case_memory",
            query_vector=get_embedding(client_name),
            limit=3,
            with_payload=True
        )
        return results

    except Exception as e:
        st.warning("Could not retrieve client history.")
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
# SAVE REPORT (NO REFLECTION ANYMORE)
# -----------------------------
if st.button(f"💾 {T['save']}"):

    if not report.strip():
        st.warning("Please enter a report.")
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

    # Save to Qdrant (permanent memory)
    qdrant.upsert(
        collection_name="reflective_case_memory",
        points=[PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload=payload
        )]
    )

    # Save to SESSION memory (today's work)
    st.session_state.today_reports.append({
        "text": report,
        "client_name": client_name,
        "embedding": embedding,
        "payload": payload
    })

    st.success("Saved successfully.")

# -----------------------------
# DAILY REFLECTION SESSION
# -----------------------------
st.markdown("---")

if st.button(f"🧠 {T['daily']}"):

    if len(st.session_state.today_reports) == 0:
        st.info("No reports in today's session yet.")
        st.stop()

    today = st.session_state.today_reports

    # Build structured reflection input
    reflection_input = ""
    all_clients = {}

    for r in today:
        client = r["client_name"]
        if client not in all_clients:
            all_clients[client] = []
        all_clients[client].append(r)

    # Build memory context
    memory_context = ""

    for client, reports in all_clients.items():

        history = get_client_history(client)

        memory_context += f"\n\nCLIENT: {client}\n"

        memory_context += "\nTODAY'S REPORTS:\n"
        for r in reports:
            memory_context += f"- {r['text']}\n"

        if history:
            memory_context += "\nPAST HISTORY (RAG):\n"
            for h in history:
                p = h.payload
                memory_context += f"- {p.get('date')} : {p.get('report_text')}\n"
        else:
            memory_context += "\nPAST HISTORY: First contact (no previous records)\n"

    system_prompt = f"""
You are a reflective practice assistant for social workers.

You do NOT evaluate performance.
You do NOT judge quality.
You support professional reflection and learning.

Structure your response:

1. Patterns Across Today's Practice
2. Client Continuity & Change (using history if available)
3. Client Voice Analysis
4. Expanding Lens (bias, assumptions, alternative explanations)
5. Evidence & Missing Information
6. Practice Reflection
7. Reflective Questions

Focus on:
- patterns across cases
- development over time (if history exists)
- balance of client vs professional voice
- assumptions and interpretation
"""

    with st.spinner("Generating reflection..."):

        response = claude.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=1200,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": f"DAILY PRACTICE DATA:\n{memory_context}"
            }]
        )

    st.markdown("---")
    st.markdown("### 🧠 Daily Reflection")

    st.markdown(
        f'<div class="reflection-card">{response.content[0].text}</div>',
        unsafe_allow_html=True
    )

# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:
    st.markdown("### 📊 Today's Session")

    st.write(f"Reports today: {len(st.session_state.today_reports)}")

    st.markdown("---")
    st.caption("Reflective Practice Companion · Session-based Prototype")
