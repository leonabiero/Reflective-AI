# ==========================================================
# SIDEBAR SUMMARY
# ==========================================================

st.sidebar.markdown(f"### 🧠 {T['today']}")

st.sidebar.write(
    f"📄 {T['reports_today']}: {len(st.session_state.draft_reports)}"
)

if st.session_state.draft_reports:

    st.sidebar.markdown("---")

    for d in st.session_state.draft_reports:

        st.sidebar.write(f"• {d['client_name']}")

st.sidebar.markdown("---")

st.sidebar.caption("Reflective Practice Companion")
