import streamlit as st

def make_fit_screen():
    st.markdown("""
        <style>
            .block-container {
                padding-top: 1rem;
                padding-bottom: 0rem;
                height: 100vh;
            }
            body {
                overflow: hidden;
            }
            .stTextArea textarea {
                height: 180px !important;
            }
        </style>
    """, unsafe_allow_html=True)