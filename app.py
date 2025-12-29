import streamlit as st
from src.views.input_ui import render_input
from src.views.choice_ui import render_choice
from src.views.output_ui import render_dashboard

# Configuration
st.set_page_config(page_title="Murphy", layout="wide")

# Initialize State
if "page" not in st.session_state:
    st.session_state.page = "INPUT"
if "user_input" not in st.session_state:
    st.session_state.user_input = {}
if "llm_responses" not in st.session_state:
    st.session_state.llm_responses = {}

# Routing Logic
if st.session_state.page == "INPUT":
    render_input()
elif st.session_state.page == "CHOICE":
    render_choice()
elif st.session_state.page == "DASHBOARD":
    render_dashboard()