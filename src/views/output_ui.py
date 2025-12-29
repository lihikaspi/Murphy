import streamlit as st

def render_dashboard():
    # Header
    st.markdown(f"### {st.session_state.llm_responses.get('title', 'Strategic Analysis')}")

    # TOP ROW: Plan vs Analysis [1, 2] ratio
    col1, col2 = st.columns([1, 2])

    with col1:
        st.text_area(
            "Input Plan",
            value=st.session_state.user_input.get('plan', ''),
            height=140,
            disabled=True
        )
        st.text_area(
            "Revised Plan",
            value=st.session_state.llm_responses.get('revised_plan', ''),
            height=140,
            disabled=True
        )

    with col2:
        st.text_area(
            "Identified Problems",
            value=st.session_state.llm_responses.get('problems', ''),
            height=140,
            disabled=True
        )
        st.text_area(
            "Detailed Improvements",
            value=st.session_state.llm_responses.get('improvements', ''),
            height=140,
            disabled=True
        )

    st.divider()

    # BOTTOM ROW: History vs Feedback & Controls
    col3, col4 = st.columns([1, 2])

    with col3:
        history_text = st.session_state.get('history_text', '')
        st.text_area("Notes History", value=history_text, height=200, disabled=True)

    with col4:
        new_notes = st.text_area("Add New Notes", placeholder="Enter feedback or corrections...", height=100)

        # Simplified controls row without the New Session button
        ctrl_col1, ctrl_col2 = st.columns([3, 1])

        with ctrl_col1:
            st.selectbox(
                "Pessimism Level",
                ["High", "Normal", "Low"],
                index=1,
                label_visibility="collapsed"
            )

        with ctrl_col2:
            if st.button("Update", type="primary", use_container_width=True):
                # Placeholder for update logic
                st.toast("Updating plan...")
                pass