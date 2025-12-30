import streamlit as st


def apply_custom_styles():
    """Applies global CSS to ensure a zero-scroll, viewport-fitted experience with a dense sidebar."""
    st.markdown("""
        <style>
            /* 1. Global Viewport Lock */
            html, body, [data-testid="stAppViewContainer"] {
                height: 100vh !important;
                width: 100vw !important;
                overflow: hidden !important;
                margin: 0;
                padding: 0;
            }

            /* Fix for Streamlit top bar overlap */
            header[data-testid="stHeader"] {
                background: transparent !important;
                z-index: 1;
            }

            /* 2. Main content container padding and height control */
            /* 'border-box' ensures padding doesn't add to the 100vh height */
            .block-container {
                padding-top: 3.5rem !important; 
                padding-bottom: 6rem !important; /* Significantly increased padding to ensure bottom clarity */
                padding-left: 3rem !important;
                padding-right: 3rem !important;
                height: 100vh !important;
                max-height: 100vh !important;
                display: flex;
                flex-direction: column;
                box-sizing: border-box !important;
            }

            /* 3. Sidebar Optimization - Dense & Minimal Spacing */
            [data-testid="stSidebar"] {
                background-color: #f8f9fb;
            }

            [data-testid="stSidebarUserContent"] {
                padding-top: 0rem !important;
                padding-left: 0.5rem !important;
                padding-right: 0.5rem !important;
                height: 100vh !important;
                display: flex;
                flex-direction: column;
                box-sizing: border-box !important;
            }

            /* Balanced gap between components in the sidebar */
            [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
                gap: 0.5rem !important;
            }

            /* Compact Header Title */
            .centered-title {
                text-align: center;
                font-size: 1.4rem;
                font-weight: 800;
                margin-top: -0.5rem !important;
                margin-bottom: 0.2rem !important;
                color: #1E1E1E;
            }

            /* Logo sizing constraint - Centered and pinned */
            [data-testid="stSidebar"] .stImage img {
                max-height: 100px;
                width: auto !important;
                object-fit: contain;
                display: block;
                margin: 0 auto !important;
            }

            /* Minimize Divider space in Sidebar */
            [data-testid="stSidebar"] hr {
                margin: 0.5rem 0 !important;
            }

            /* 4. Scrollable Scenario Box (for Choice Page) */
            .scroll-container {
                max-height: 18vh; /* Further reduced to prioritize button visibility */
                overflow-y: auto;
                background: #f0f2f6;
                padding: 1rem;
                border-radius: 0.5rem;
                border: 1px solid #ddd;
                margin-bottom: 0.5rem;
            }

            /* 5. Compact Components */
            .stTextArea textarea {
                resize: none !important;
                font-size: 0.9rem !important;
            }

            [data-testid="stForm"] {
                display: flex;
                flex-direction: column;
                flex-grow: 1;
                border: none !important;
                padding: 0 !important;
            }

            /* 6. Hide default scrollbars globally */
            ::-webkit-scrollbar {
                display: none !important;
            }
            * {
                scrollbar-width: none !important;
                -ms-overflow-style: none !important;
            }
        </style>
    """, unsafe_allow_html=True)