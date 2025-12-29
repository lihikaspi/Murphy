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
    page_icon_img = None  # Fallback
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

    ### 🛠️ Button Explanations
    * **Edit User Input**: Navigates back to the first page. Your current text is saved so you can tweak your plan without starting over.
    * **Clear Session**: Completely wipes the current session. Use this if you want to start a brand new project from scratch.
    * **Update (Dashboard)**: Refines the current analysis based on the "New Notes" you provided.
    * **Send (Input Page)**: Submits your data to the LLM to begin the simulation.
    """)


# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    # Top Header Section
    st.markdown('<div class="sidebar-header">', unsafe_allow_html=True)
    if logo_img:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(logo_img, use_container_width=True)
    st.markdown('<h1 class="centered-title">Murphy</h1>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Navigation Buttons
    if st.button("Edit User Input", use_container_width=True):
        st.session_state.page = "INPUT"
        st.rerun()

    if st.button("Clear Session", use_container_width=True):
        st.session_state.user_input = {}
        st.session_state.llm_responses = {}
        st.session_state.history_text = ""
        st.session_state.page = "INPUT"
        st.rerun()

    # Pushes the help button to the bottom
    st.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)

    # Bottom Help Section
    st.markdown("---")
    if st.button("Help & Info", use_container_width=True):
        show_help()

# Routing Logic
if st.session_state.page == "INPUT":
    render_input()
elif st.session_state.page == "CHOICE":
    render_choice()
elif st.session_state.page == "DASHBOARD":
    render_dashboard()