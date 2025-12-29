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

# Apply global styling (handles centering and tooltip wrapping)
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
    # Use a container to group the logo and title for CSS targeting
    st.markdown('<div class="sidebar-header">', unsafe_allow_html=True)
    if img:
        # Centering the image using columns or Markdown/HTML
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(img, use_container_width=True)

    # Custom HTML for centered title
    st.markdown('<h1 class="centered-title">Murphy</h1>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # 1. Back Button with Tooltip (Preserves Data)
    if st.button(
            "Edit User Input",
            use_container_width=True,
            help="Navigates back to the input form while preserving your current text."
    ):
        st.session_state.page = "INPUT"
        st.rerun()

    # 2. New Session Button with Tooltip (Resets Data)
    if st.button(
            "Clear Session",
            use_container_width=True,
            help="Begins a new session and clears all current inputs and analysis summary."
    ):
        st.session_state.user_input = {}
        st.session_state.llm_responses = {}
        st.session_state.history_text = ""
        st.session_state.page = "INPUT"
        st.rerun()

# Routing Logic
if st.session_state.page == "INPUT":
    render_input()
elif st.session_state.page == "CHOICE":
    render_choice()
elif st.session_state.page == "DASHBOARD":
    render_dashboard()