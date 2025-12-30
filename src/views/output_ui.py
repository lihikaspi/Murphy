import streamlit as st


def render_dashboard():
    # Header with minimal margin
    st.markdown(f"### 🛡️ {st.session_state.llm_responses.get('title', 'Project Fortification Dashboard')}")

    # Main Grid - Using 2 large columns for the top section
    # We use height constraints on text areas to ensure they stay on one screen
    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        st.caption("Your Strategy")
        st.text_area("Original Plan", value=st.session_state.user_input.get('plan', ''), height=180, disabled=True)
        st.text_area("Optimized Plan", value=st.session_state.llm_responses.get('revised_plan', ''), height=180,
                     disabled=True)

    with row1_col2:
        st.caption("Risk Analysis")
        st.text_area("Critical Failures Identified", value=st.session_state.llm_responses.get('problems', ''),
                     height=180, disabled=True)
        st.text_area("Actionable Improvements", value=st.session_state.llm_responses.get('improvements', ''),
                     height=180, disabled=True)

    st.markdown("---")

    # Interactive Footer
    row2_col1, row2_col2 = st.columns([1, 1.5])

    with row2_col1:
        st.caption("Timeline History")
        history_text = st.session_state.get('history_text', 'No previous history.')
        st.text_area("Decision Log", value=history_text, height=120, disabled=True, label_visibility="collapsed")

    with row2_col2:
        st.caption("Iterative Refinement")
        new_notes = st.text_area("Add Feedback", placeholder="How can we refine this further?", height=80,
                                 label_visibility="collapsed")

        btn_col1, btn_col2 = st.columns([2, 1])
        with btn_col1:
            st.selectbox("Adjustment Level", ["High Risk", "Moderate", "Conservative"], index=1,
                         label_visibility="collapsed")
        with btn_col2:
            if st.button("Update Analysis", type="primary", use_container_width=True):
                st.toast("Processing new insights...")