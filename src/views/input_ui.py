import streamlit as st


def render_input():
    st.title("Murphy")

    # Fetch existing values from state to preserve input
    data = st.session_state.get("user_input", {})

    with st.form("input_form"):
        # Setting 'value' to state variables ensures they stay filled when navigating back
        about = st.text_area("Tell me about yourself", value=data.get("about", ""), height=100)
        goal = st.text_area("What do you want to achieve", value=data.get("goal", ""), height=100)
        plan = st.text_area("How are you planning on doing that", value=data.get("plan", ""), height=100)
        wrong = st.text_area("What do you think could go wrong?", value=data.get("wrong", ""), height=100)

        # Grid for the bottom row
        col1, col2 = st.columns([2, 1])
        with col1:
            pessimism = st.select_slider("Pessimism level", options=[1, 2, 3, 4, 5], value=data.get("pessimism", 3))
        with col2:
            st.write("##")  # alignment
            submitted = st.form_submit_button("Send", type="primary", use_container_width=True)

        if submitted:
            # Save to state
            st.session_state.user_input = {
                "about": about,
                "goal": goal,
                "plan": plan,
                "wrong": wrong,
                "pessimism": pessimism
            }
            # Change page
            st.session_state.page = "CHOICE"
            st.rerun()