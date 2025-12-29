import streamlit as st


def render_input():
    st.title("Murphy")
    with st.form("input_form"):
        about = st.text_area("Tell me about yourself")
        goal = st.text_area("What do you want to achieve")
        plan = st.text_area("How are you planning on doing that")
        wrong = st.text_area("What do you think could go wrong?")

        # Grid for the bottom row
        col1, col2 = st.columns([2, 1])
        with col1:
            pessimism = st.select_slider("Pessimism level", options=[1, 2, 3, 4, 5])
        with col2:
            submitted = st.form_submit_button("Send")

        if submitted:
            st.session_state.user_input = {"about": about, "goal": goal, "plan": plan, "wrong": wrong}
            st.session_state.page = "CHOICE"
            st.rerun()