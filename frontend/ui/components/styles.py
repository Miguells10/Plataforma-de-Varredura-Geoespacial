import streamlit as st


def apply_custom_styles():
    st.markdown("""
        <style>
        /* Card Cyberpunk */
        .metric-card { 
            background-color: #0E1117; 
            border: 1px solid #333; 
            border-left: 5px solid #00c0f2; 
            padding: 15px; 
            border-radius: 8px; 
            color: white; 
            margin-bottom: 10px; 
        }

        /* Abas Estilizadas */
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] { 
            height: 50px; 
            white-space: pre-wrap; 
            background-color: #1c1f26; 
            border-radius: 5px; 
            color: #a0a0a0;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #00c0f2 !important;
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)