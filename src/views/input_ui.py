import streamlit as st


def render_input():
    # Fetch existing values from state
    data = st.session_state.get("user_input", {})

    st.subheader("Plan Your Future")

    with st.form("input_form", clear_on_submit=False):
        # Using columns to distribute fields horizontally if needed,
        # or keeping them stacked but with smaller heights to fit screen
        col_top1, col_top2 = st.columns(2)
        with col_top1:
            about = st.text_area("Tell me about yourself", value=data.get("about", ""), height=130,
                                 placeholder="Who are you?")
            goal = st.text_area("What do you want to achieve", value=data.get("goal", ""), height=130,
                                placeholder="Your primary objective...")

        with col_top2:
            plan = st.text_area("How are you planning on doing that", value=data.get("plan", ""), height=130,
                                placeholder="Step-by-step strategy...")
            wrong = st.text_area("What do you think could go wrong?", value=data.get("wrong", ""), height=130,
                                 placeholder="Identify obvious risks...")

        st.write("")  # Spacer

        # Bottom row for parameters and submit
        col_bot1, col_bot2 = st.columns([3, 1])
        with col_bot1:
            pessimism = st.select_slider("Pessimism Level (1 = Optimistic, 5 = Murphy's Law)",
                                         options=[1, 2, 3, 4, 5],
                                         value=data.get("pessimism", 3))
        with col_bot2:
            st.write("##")  # Manual vertical alignment
            submitted = st.form_submit_button("Initiate Stress Test", type="primary", use_container_width=True)

        if submitted:
            st.session_state.user_input = {
                "about": about,
                "goal": goal,
                "plan": plan,
                "wrong": wrong,
                "pessimism": pessimism
            }
            st.session_state.page = "CHOICE"
            st.rerun()