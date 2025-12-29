import streamlit as st


def apply_custom_styles():
    """Applies global CSS to fix page height and style components."""
    st.markdown("""
        <style>
            /* Force Wide Mode padding reduction */
            .block-container {
                padding-top: 2rem !important;
                padding-bottom: 0rem !important;
                max-height: 100vh;
            }

            /* Hide main scrollbar if possible */
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