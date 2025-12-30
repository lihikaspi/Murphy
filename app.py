import streamlit as st
from PIL import Image
from src.views.input_ui import render_input
from src.views.choice_ui import render_choice
from src.views.output_ui import render_dashboard
from src.styles import apply_custom_styles

# Configuration - Must be the first Streamlit command
try:
    page_icon_img = Image.open("images/broken_clock_handle.png")
    logo_img = Image.open("images/broken_clock.png")
except:
    page_icon_img = None
    logo_img = None

st.set_page_config(page_title="Murphy", page_icon=page_icon_img, layout="wide")

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


# --- HELP DIALOG ---
@st.dialog("How to use Murphy")
def show_help():
    st.markdown("""
    ### 🚀 Getting Started
    Murphy is a pre-mortem simulator designed to stress-test your plans.
    1. **Input Phase**: Tell Murphy about your goal and your plan.
    2. **Stress Test**: Murphy will present "Failed Timelines"—scenarios where things went wrong.
    3. **Dashboard**: Review the revised strategy and improvements based on your reactions.
    """)


# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    # Top section: Logo and Title (pinned to top)
    if logo_img:
        # width='content' ensures the CSS centering logic (margin: 0 auto)
        # correctly aligns the image horizontally without stretching it.
        st.image(logo_img, width='content')

    st.markdown('<h1 class="centered-title">Murphy</h1>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)  # Space between header and buttons
    st.markdown("---")
    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)  # Space after divider

    # Navigation and Action Buttons
    if st.button("Edit User Input", width='stretch'):
        st.session_state.page = "INPUT"
        st.rerun()

    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)  # Subtle extra spacing

    if st.button("Clear Session", width='stretch'):
        st.session_state.user_input = {}
        st.session_state.llm_responses = {}
        st.session_state.history_text = ""
        st.session_state.page = "INPUT"
        st.rerun()

    # Divider between actions and help
    st.markdown("---")
    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)  # Space after divider

    if st.button("Help & Info", width='stretch'):
        show_help()

# Routing Logic
if st.session_state.page == "INPUT":
    render_input()
elif st.session_state.page == "CHOICE":
    render_choice()
elif st.session_state.page == "DASHBOARD":
    render_dashboard()