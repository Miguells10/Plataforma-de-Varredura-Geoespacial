import streamlit as st

# --- CONSTANTES ---
API_BASE_URL = "http://localhost:8000"
APP_TITLE = "Radix GeoIntelligence"
APP_ICON = "⚡"


# --- ESTILOS GLOBAIS (O Cyberpunk voltou) ---
def apply_custom_css():
    st.markdown("""
    <style>
        /* Fundo e Texto */
        .stApp { background-color: #0e1117; color: #fafafa; }

        /* Ajuste de Padding */
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }

        /* Cards de Métricas (KPIs) */
        div[data-testid="metric-container"] {
            background-color: #1a1c24;
            border: 1px solid #333;
            padding: 15px;
            border-radius: 8px;
            border-left: 5px solid #00c0f2;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }

        /* Botão Primário (Neon Blue) */
        .stButton button {
            background-color: #00c0f2;
            color: white;
            font-weight: bold;
            border: none;
            transition: all 0.3s ease;
        }
        .stButton button:hover {
            background-color: #0090b5;
            box-shadow: 0 0 10px #00c0f2;
        }

        /* Abas Estilizadas */
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #1c1f26;
            border-radius: 5px;
            color: #a0a0a0;
            border: 1px solid #333;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #00c0f2 !important;
            color: white !important;
            border-color: #00c0f2;
        }
    </style>
    """, unsafe_allow_html=True)