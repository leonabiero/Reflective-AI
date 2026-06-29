# ==========================================================
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
