import streamlit as st


def apply_custom_styles():
    """Applies global CSS for height, component styling, and centering the sidebar header."""
    st.markdown("""
        <style>
            /* 1. Sidebar Layout & Bottom Alignment */
            [data-testid="stSidebarUserContent"] {
                padding-top: 0rem !important; /* Removed space from above the logo */
                display: flex;
                flex-direction: column;
                height: 100vh !important;
                overflow-y: hidden !important;
            }

            /* This div acts as a flexible spacer to push content below it to the bottom */
            .sidebar-spacer {
                flex-grow: 1;
            }

            /* 2. Centered Logo and Title */
            [data-testid="stSidebar"] div.stImage {
                display: flex;
                justify-content: center;
                margin-top: 0px !important;
                margin-bottom: 5px !important;
            }

            .centered-title {
                text-align: center;
                font-size: 2rem;
                font-weight: 700;
                margin-top: 0px !important;
                margin-bottom: 5px !important;
                color: #31333F;
            }

            /* 3. Spacing for dividers and buttons */
            [data-testid="stSidebar"] hr {
                margin-top: 0.8rem !important;
                margin-bottom: 1.5rem !important;
            }

            [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
                gap: 0.5rem !important;
            }

            /* 4. Fit sidebar to screen and hide scrollbars */
            [data-testid="stSidebar"], 
            [data-testid="stSidebar"] > div:first-child {
                overflow: hidden !important;
                scrollbar-width: none !important;
                height: 100vh !important;
            }

            [data-testid="stSidebar"]::-webkit-scrollbar {
                display: none !important;
            }

            /* 5. Dashboard card styling */
            .stTextArea textarea:disabled {
                background-color: #f8f9fa !important;
                color: #333 !important;
                border: 1px solid #ddd !important;
            }

            /* 6. Make st.dialog (popup) wider */
            div[role="dialog"] {
                width: 60vw !important;
                max-width: 1000px !important;
            }

            /* Global padding reduction */
            .block-container {
                padding-top: 2rem !important;
                padding-bottom: 0rem !important;
                max-height: 100vh;
            }

            body {
                overflow: hidden;
            }
        </style>
    """, unsafe_allow_html=True)