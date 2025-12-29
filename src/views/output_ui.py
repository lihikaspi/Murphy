import streamlit as st


def render_dashboard():
    # Header from your sketch/Gradio HTML
    st.markdown(f"### {st.session_state.llm_responses.get('title', 'Strategic Analysis')}")

    # TOP ROW: Plan vs Analysis
    # In Gradio you had scale 1 and 2. In Streamlit: [1, 2]
    col1, col2 = st.columns([1, 2])

    with col1:
        # The Plan (Input)
        st.text_area(
            "Input Plan",
            value=st.session_state.user_input.get('plan', ''),
            height=150,
            disabled=True
        )
        # Revised Plan
        st.text_area(
            "Revised Plan",
            value=st.session_state.llm_responses.get('revised_plan', ''),
            height=150,
            disabled=True
        )

    with col2:
        # Identified Problems
        st.text_area(
            "Identified Problems",
            value=st.session_state.llm_responses.get('problems', ''),
            height=150,
            disabled=True
        )
        # Detailed Improvements
        st.text_area(
            "Detailed Improvements",
            value=st.session_state.llm_responses.get('improvements', ''),
            height=150,
            disabled=True
        )

    st.divider()

    # BOTTOM ROW: History vs Feedback & Controls
    col3, col4 = st.columns([1, 2])

    with col3:
        # Notes History
        history_text = st.session_state.get('history_text', '')
        st.text_area("Notes History", value=history_text, height=200, disabled=True)

    with col4:
        # Add New Notes (The bigger box in your sketch)
        new_notes = st.text_area("Add New Notes", placeholder="Enter feedback or corrections...", height=120)

        # Bottom controls (Dropdown and Buttons)
        # We split col4 into smaller sub-columns to match the horizontal alignment
        ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 1, 1])

        with ctrl_col1:
            output_pessimism = st.selectbox(
                "Pessimism Level",
                ["High", "Normal", "Low"],
                index=1
            )

        with ctrl_col2:
            st.write("##")  # Visual alignment spacer
            if st.button("Update", type="primary", use_container_width=True):
                # Function call logic goes here
                pass

        with ctrl_col3:
            st.write("##")  # Visual alignment spacer
            if st.button("New", use_container_width=True):
                st.session_state.page = "INPUT"
                st.rerun()