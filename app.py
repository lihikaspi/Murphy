import streamlit as st
from PIL import Image
from src.views.input_ui import render_input
from src.views.choice_ui import render_choice
from src.views.output_ui import render_dashboard
from src.styles import apply_custom_styles

# Configuration - Must be the first Streamlit command
try:
    img = Image.open("images/broken_clock.png")
except:
    img = None  # Fallback if image is missing

st.set_page_config(page_title="Murphy", page_icon=img, layout="wide")

# Apply global styling
apply_custom_styles()

# Initialize State
if "page" not in st.session_state:
    st.session_state.page = "INPUT"
if "user_input" not in st.session_state:
    st.session_state.user_input = {}
if "llm_responses" not in st.session_state:
    st.session_state.llm_responses = {}
if "history_text" not in st.session_state:
    st.session_state.history_text = ""

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    if img:
        st.image(img, width=100)
    st.title("Murphy")
    st.markdown("---")

    # 1. Back Button (Preserves Data)
    if st.button("Edit User Input", use_container_width=True):
        st.session_state.page = "INPUT"
        st.rerun()

    # 2. New Session Button (Resets Data)
    if st.button("Clear Session", use_container_width=True):
        st.session_state.user_input = {}
        st.session_state.llm_responses = {}
        st.session_state.history_text = ""
        st.session_state.page = "INPUT"
        st.rerun()

    st.markdown("---")
    st.info(" 'Edit User Input' navigates back to the input form.\n'Clear Session' begins a new session.")

# Routing Logic
if st.session_state.page == "INPUT":
    render_input()
elif st.session_state.page == "CHOICE":
    render_choice()
elif st.session_state.page == "DASHBOARD":
    render_dashboard()