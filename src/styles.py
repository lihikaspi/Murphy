import streamlit as st

def apply_custom_styles():
    """Applies global CSS to ensure a zero-scroll, viewport-fitted experience."""
    st.markdown("""
        <style>
            /* 1. Reset Body and Container to Viewport Height */
            html, body, [data-testid="stAppViewContainer"] {
                height: 100vh;
                overflow: hidden !important;
            }

            /* 2. Main content container padding and height control */
            .block-container {
                padding-top: 1.5rem !important;
                padding-bottom: 1.5rem !important;
                padding-left: 3rem !important;
                padding-right: 3rem !important;
                height: 100vh !important;
                display: flex;
                flex-direction: column;
            }

            /* 3. Force st.form and other containers to be flexible */
            [data-testid="stForm"] {
                display: flex;
                flex-direction: column;
                flex-grow: 1;
                border: none !important;
                padding: 0 !important;
            }

            /* 4. Sidebar optimization */
            [data-testid="stSidebarUserContent"] {
                display: flex;
                flex-direction: column;
                height: 100vh !important;
            }

            .sidebar-spacer {
                flex-grow: 1;
            }

            .centered-title {
                text-align: center;
                font-size: 1.8rem;
                font-weight: 700;
                margin-bottom: 0px !important;
                color: #31333F;
            }

            /* 5. Compact TextArea & Grid Adjustments */
            .stTextArea textarea {
                resize: none !important;
            }

            /* 6. Hide default scrollbars globally */
            ::-webkit-scrollbar {
                display: none !important;
            }
            * {
                scrollbar-width: none !important;
                -ms-overflow-style: none !important;
            }

            /* 7. Dialog/Popup sizing */
            div[role="dialog"] {
                width: 70vw !important;
                max-width: 900px !important;
            }
        </style>
    """, unsafe_allow_html=True)