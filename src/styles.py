import streamlit as st


def apply_custom_styles():
    """Applies global CSS for height, component styling, and centering the sidebar header."""
    st.markdown("""
        <style>
            /* Tooltip fix: Reposition to the right side and allow text wrapping */
            div[data-testid="stTooltipHoverTarget"] + div {
                white-space: normal !important;
                max-width: 200px !important;
                word-wrap: break-word !important;
                /* Attempt to force position to the right */
                left: 100% !important;
                top: 50% !important;
                transform: translate(15px, -50%) !important;
            }

            /* Target the specific tooltip content container in Streamlit */
            .stTooltipContent {
                max-width: 200px !important;
                white-space: normal !important;
            }

            /* Ensure the tooltip arrow (if any) is hidden or adjusted */
            div[data-testid="stTooltipHoverTarget"] + div > div:first-child {
                display: none !important;
            }

            /* Centering the Sidebar Logo and Title */
            .centered-title {
                text-align: center;
                font-size: 2rem;
                font-weight: 700;
                margin-top: -10px;
                margin-bottom: 0px !important;
                padding-bottom: 0px !important;
                color: #31333F;
            }

            [data-testid="stSidebar"] div.stImage {
                display: flex;
                justify-content: center;
                margin-bottom: 5px !important;
            }

            /* Standardize spacing for dividers to reduce density */
            [data-testid="stSidebar"] hr {
                margin-top: 1.5rem !important;
                margin-bottom: 1.5rem !important;
            }

            [data-testid="stSidebar"] .stButton {
                margin-top: 2px !important;
                margin-bottom: 2px !important;
            }

            /* Vertical block gap refinement */
            [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
                gap: 0.75rem !important;
            }

            /* Fit sidebar to screen and hide ALL scrollbars */
            [data-testid="stSidebar"], 
            [data-testid="stSidebar"] > div:first-child {
                overflow: hidden !important;
                scrollbar-width: none !important;
                -ms-overflow-style: none !important;
                height: 100vh !important;
            }

            [data-testid="stSidebar"]::-webkit-scrollbar {
                display: none !important;
            }

            /* Force Wide Mode padding reduction */
            .block-container {
                padding-top: 2rem !important;
                padding-bottom: 0rem !important;
                max-height: 100vh;
            }

            /* Hide main scrollbar */
            body {
                overflow: hidden;
            }

            /* Style disabled text areas for dashboard look */
            .stTextArea textarea:disabled {
                background-color: #f8f9fa !important;
                color: #333 !important;
                border: 1px solid #ddd !important;
            }

            /* Remove excess space above subheaders */
            h3 {
                margin-top: 0px !important;
            }
        </style>
    """, unsafe_allow_html=True)