import streamlit as st


def render_choice():
    st.header("Scenario from Failed Timeline")
    st.write("The LLM generated scenario goes here...")

    # Implementing your sketch buttons
    choice = st.radio("What would you do?", ["Option A", "Option B", "Option C", "Other"])

    if choice == "Other":
        other_text = st.text_input("Enter here", placeholder="Type your custom response...")

    if st.button("Submit Choice"):
        # Logic to either show next scenario or move to dashboard
        st.session_state.page = "DASHBOARD"
        st.rerun()