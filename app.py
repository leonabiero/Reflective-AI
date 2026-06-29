import streamlit as st
from anthropic import Anthropic
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

import uuid
import re

from datetime import datetime
from collections import defaultdict

# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="Reflective Practice Companion",
    page_icon="🧠",
    layout="centered"
)

# ==========================================================
# CUSTOM CSS
# ==========================================================

st.markdown("""
<style>

.stApp{
    background:#1A1A2E;
}

/* Sidebar */

[data-testid="stSidebar"]{
    background:#16213E;
}

/* Main title */

h1{
    color:#AFA9EC;
    text-align:center;
    font-family:Georgia, serif;
    font-size:2rem !important;
    white-space:nowrap;
    margin-bottom:0.3rem;
}

/* Section titles */

h2,h3{
    color:#7F77DD;
    font-family:Georgia, serif;
}

/* Text */

p,div,label{
    color:#CECBF6;
}

/* Text areas */

textarea{
    background:#26215C !important;
    color:#EEEDFE !important;
    border-radius:10px !important;
}

/* Buttons */

.stButton>button{

    width:100%;

    background:#7F77DD;

    color:white;

    border:none;

    border-radius:8px;

    padding:0.65rem;

    font-weight:600;
}

/* Reflection card */

.reflection-card{

    background:#26215C;

    border:1px solid #534AB7;

    border-radius:12px;

    padding:1.2rem;

    color:#EEEDFE;

    margin-top:15px;

    margin-bottom:15px;
}

/* Better metric colours */

[data-testid="stMetricValue"]{
    color:white;
}

[data-testid="stMetricLabel"]{
    color:#CECBF6;
}

</style>
""", unsafe_allow_html=True)

# ==========================================================
# LANGUAGE SYSTEM
# ==========================================================

LANGUAGES = {

"Español":{

"title":"🧠 ACOMPAÑANTE DE PRÁCTICA REFLEXIVA",

"subtitle":"Apoyo a la reflexión profesional en trabajo social",

"client":"Nombre del cliente",

"report":"Informe de intervención",

"placeholder":"Escriba o pegue aquí el informe de intervención...",

"save_draft":"💾 Guardar borrador",

"draft_saved":"Borrador guardado correctamente.",

"draft_empty":"Por favor escriba un informe.",

"daily":"🧠 Iniciar reflexión diaria",

"today":"Sesión de hoy",

"reports_today":"Informes de hoy",

"no_reports":"Todavía no hay informes.",

"reflection":"Reflexión diaria",

"review":"Revisar informes",

"submit":"Enviar informes",

"submit_without":"Enviar sin cambios",

"edit":"Editar antes de enviar",

"reflection_loading":"Analizando la práctica del día...",

"language":"Idioma"

},

"Euskara":{

"title":"🧠 HAUSNARKETA PRAKTIKAREN LAGUNA",

"subtitle":"Gizarte-laneko hausnarketa profesionalerako laguntza",

"client":"Bezeroaren izena",

"report":"Esku-hartze txostena",

"placeholder":"Idatzi edo itsatsi esku-hartze txostena hemen...",

"save_draft":"💾 Zirriborroa gorde",

"draft_saved":"Zirriborroa ondo gorde da.",

"draft_empty":"Mesedez idatzi txosten bat.",

"daily":"🧠 Hasi eguneroko hausnarketa",

"today":"Gaurko saioa",

"reports_today":"Gaurko txostenak",

"no_reports":"Oraindik ez dago txostenik.",

"reflection":"Eguneko hausnarketa",

"review":"Txostenak berrikusi",

"submit":"Txostenak bidali",

"submit_without":"Aldaketarik gabe bidali",

"edit":"Bidali aurretik editatu",

"reflection_loading":"Gaurko jarduna aztertzen...",

"language":"Hizkuntza"

},

"English":{

"title":"🧠 REFLECTIVE PRACTICE COMPANION",

"subtitle":"Supporting professional reflection in social work",

"client":"Client Name",

"report":"Intervention Report",

"placeholder":"Write or paste the intervention report here...",

"save_draft":"💾 Save Draft",

"draft_saved":"Draft saved successfully.",

"draft_empty":"Please enter a report.",

"daily":"🧠 Start Daily Reflection",

"today":"Today's Session",

"reports_today":"Reports Today",

"no_reports":"No reports yet.",

"reflection":"Daily Reflection",

"review":"Review Reports",

"submit":"Submit Reports",

"submit_without":"Submit Without Changes",

"edit":"Edit Before Submission",

"reflection_loading":"Analysing today's practice...",

"language":"Language"

}

}

# Spanish first

language = st.sidebar.selectbox(

f"🌐 {LANGUAGES['Español']['language']}",

list(LANGUAGES.keys()),

index=0

)

T = LANGUAGES[language]

# ==========================================================
# CONFIGURATION
# ==========================================================

QDRANT_URL = st.secrets["QDRANT_URL"]

QDRANT_API_KEY = st.secrets["QDRANT_API_KEY"]

ANTHROPIC_API_KEY = st.secrets["ANTHROPIC_API_KEY"]

claude = Anthropic(

api_key=ANTHROPIC_API_KEY

)

qdrant = QdrantClient(

url=QDRANT_URL,

api_key=QDRANT_API_KEY

)

embedding_model = SentenceTransformer(

"all-MiniLM-L6-v2"

)

# ==========================================================
# HELPERS
# ==========================================================

def get_embedding(text):

    return embedding_model.encode(text).tolist()


def extract_client_name(text):

    """
    Temporary helper.

    Later this can be replaced with
    a client selector connected to
    the organisation database.
    """

    match = re.search(

        r"client,\s*([A-Z][a-z]+\s[A-Z][a-z]+)",

        text

    )

    if match:

        return match.group(1)

    return "Unknown"


def today():

    return datetime.now().strftime("%Y-%m-%d")


def now():

    return datetime.now().isoformat()# ==========================================================
# SESSION STATE
# ==========================================================

if "draft_reports" not in st.session_state:
    st.session_state.draft_reports = []

if "reflection_complete" not in st.session_state:
    st.session_state.reflection_complete = False

if "reflection_text" not in st.session_state:
    st.session_state.reflection_text = ""

# ==========================================================
# HEADER
# ==========================================================

st.title(T["title"])

st.caption(T["subtitle"])

st.markdown("---")

# ==========================================================
# REPORT ENTRY
# ==========================================================

client_name = st.text_input(
    T["client"],
    placeholder="John Smith"
)

report = st.text_area(
    T["report"],
    placeholder=T["placeholder"],
    height=260
)

# ==========================================================
# SAVE DRAFT
# ==========================================================

if st.button(T["save_draft"]):

    if not report.strip():

        st.warning(T["draft_empty"])

        st.stop()

    if client_name.strip() == "":

        client_name = "Unknown"

    draft = {

        "report_id": str(uuid.uuid4()),

        "client_id": None,

        "client_name": client_name,

        "report_text": report,

        "status": "draft",

        "created_at": now(),

        "submitted_at": None,

        "reflection_completed": False,

        "language": language,

        "embedding": get_embedding(report)

    }

    st.session_state.draft_reports.append(draft)

    st.success(T["draft_saved"])

# ==========================================================
# TODAY'S DRAFTS
# ==========================================================

st.markdown("---")

st.subheader(f"📂 {T['today']}")

if len(st.session_state.draft_reports) == 0:

    st.info(T["no_reports"])

else:

    st.write(
        f"**{T['reports_today']}: {len(st.session_state.draft_reports)}**"
    )

    for i, draft in enumerate(st.session_state.draft_reports):

        with st.expander(

            f"📄 {draft['client_name']}"

        ):

            st.write(

                draft["report_text"]

            )

# ==========================================================
# START DAILY REFLECTION
# ==========================================================

st.markdown("---")

start_reflection = st.button(

    T["daily"]

)# ==========================================================
# CLIENT HISTORY (RAG)
# ==========================================================

def get_client_history(client_name):

    """
    Retrieves past reports for a client from Qdrant.
    This is used for longitudinal reflection.
    """

    try:

        # We use a simple semantic search over client name
        results = qdrant.search(
            collection_name="reflective_case_memory",
            query_vector=get_embedding(client_name),
            limit=5,
            with_payload=True
        )

        return results

    except Exception:

        return []

# ==========================================================
# DAILY REFLECTION ENGINE
# ==========================================================

def build_reflection_context():

    """
    Builds structured context for Claude:
    - today's drafts
    - grouped by client
    - plus historical context (RAG)
    """

    grouped = {}

    for d in st.session_state.draft_reports:

        grouped.setdefault(d["client_name"], []).append(d)

    context = ""

    for client, reports in grouped.items():

        context += f"\n\n==============================\n"

        context += f"CLIENT: {client}\n"

        context += f"==============================\n\n"

        context += "TODAY'S REPORTS:\n"

        for r in reports:

            context += f"- {r['report_text']}\n"

        history = get_client_history(client)

        if history:

            context += "\nPAST HISTORY (RAG):\n"

            for h in history:

                p = h.payload

                context += f"- {p.get('date')} : {p.get('report_text')}\n"

        else:

            context += "\nPAST HISTORY: No previous records\n"

    return context

# ==========================================================
# CLAUDE REFLECTION PROMPT
# ==========================================================

def generate_reflection(context):

    system_prompt = f"""

You are a reflective practice companion for social workers.

You do NOT evaluate performance.
You do NOT judge correctness.

Your role is to support professional reflection.

---

STRUCTURE YOUR RESPONSE EXACTLY AS:

1. Patterns Across Today's Practice
2. The Client's Perspective in Today's Documentation
3. Client Continuity & Change (RAG insights)
4. Expanding the Lens (bias, assumptions, alternatives)
5. Evidence & Missing Information
6. Practice Reflection
7. Reflective Questions

---

IMPORTANT PRINCIPLES:

- Focus on meaning, not judgment
- Distinguish observation vs interpretation
- Highlight missing client voice where relevant
- Identify assumptions gently
- Look across time where history exists
- Never instruct or command the practitioner

"""

    response = claude.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=1400,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": context
            }
        ]
    )

    return response.content[0].text

# ==========================================================
# TRIGGER DAILY REFLECTION
# ==========================================================

if start_reflection:

    if len(st.session_state.draft_reports) == 0:

        st.info(T["no_reports"])

        st.stop()

    with st.spinner(T["reflection_loading"]):

        context = build_reflection_context()

        reflection = generate_reflection(context)

        st.session_state.reflection_text = reflection

        st.session_state.reflection_complete = True

    st.markdown("---")

    st.subheader(f"🧠 {T['reflection']}")

    st.markdown(
        f'<div class="reflection-card">{reflection}</div>',
        unsafe_allow_html=True
    )# ==========================================================
# REVIEW + SUBMISSION WORKFLOW
# ==========================================================

def save_to_qdrant(final_reports, reflection_text):

    """
    Saves FINAL (reviewed) reports into Qdrant.
    This is the organisational memory layer.
    """

    for r in final_reports:

        payload = {

            "client_id": None,

            "client_name": r["client_name"],

            "report_id": r["report_id"],

            "report_text": r["report_text"],

            "status": "submitted",

            "language": language,

            "created_at": r["created_at"],

            "submitted_at": now(),

            "reflection_used": True,

            "reflection_summary": reflection_text,

        }

        qdrant.upsert(
            collection_name="reflective_case_memory",
            points=[
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=r["embedding"],
                    payload=payload
                )
            ]
        )

# ==========================================================
# POST-REFLECTION UI
# ==========================================================

if st.session_state.reflection_complete:

    st.markdown("---")

    st.subheader("🧾 " + T["review"])

    st.write(
        "You can review your drafts before submitting them."
    )

    # Editable drafts
    edited_reports = []

    for i, d in enumerate(st.session_state.draft_reports):

        with st.expander(f"✏ {d['client_name']}"):

            edited_text = st.text_area(
                f"{T['report']} #{i+1}",
                value=d["report_text"],
                key=f"edit_{d['report_id']}"
            )

            d["report_text"] = edited_text

            edited_reports.append(d)

    # ======================================================
    # SUBMIT OPTIONS
    # ======================================================

    st.markdown("### " + T["submit"])

    col1, col2 = st.columns(2)

    with col1:

        submit_edit = st.button(T["edit"])

    with col2:

        submit_final = st.button(T["submit_without"])

    # ======================================================
    # HANDLE SUBMISSION
    # ======================================================

    if submit_edit or submit_final:

        with st.spinner("Submitting reports..."):

            save_to_qdrant(edited_reports, st.session_state.reflection_text)

            # Clear session after submission
            st.session_state.draft_reports = []

            st.session_state.reflection_complete = False

            st.session_state.reflection_text = ""

        st.success("Reports successfully submitted.")

        st.rerun()# ==========================================================
# SIDEBAR SUMMARY
# ==========================================================

with st.sidebar:

    st.markdown(f"### 🧠 {T['today']}")

    st.write(f"📄 {T['reports_today']}: {len(st.session_state.draft_reports)}")

    if st.session_state.draft_reports:

        st.markdown("---")

        for d in st.session_state.draft_reports:

            st.write(f"• {d['client_name']}")

    st.markdown("---")

    st.caption("Reflective Practice Companion")

# ==========================================================
# CLEAN RESET HANDLING (SAFETY)
# ==========================================================

def reset_session():

    """
    Optional utility for future expansion.
    Keeps system stable between reflection cycles.
    """

    st.session_state.draft_reports = []

    st.session_state.reflection_complete = False

    st.session_state.reflection_text = ""

# ==========================================================
# REFLECTION JOURNAL HOOK (FUTURE READY)
# ==========================================================

def save_reflection_journal(reflection_text):

    """
    This is NOT active yet in UI,
    but prepares your system for:
    - personal practitioner learning logs
    - organisational development insights
    """

    # Placeholder structure for future database/table

    journal_entry = {

        "id": str(uuid.uuid4()),

        "date": today(),

        "reflection": reflection_text,

        "language": language

    }

    return journal_entry

# ==========================================================
# FINAL UX POLISH NOTE (IMPORTANT DESIGN DECISION)
# ==========================================================

st.markdown("---")

st.caption(
    "All reports remain drafts until reflection and submission are completed. "
    "This system is designed to support reflective practice, not evaluation."
)
