import streamlit as st
import sys
import os
from dotenv import load_dotenv #

load_dotenv()
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from src.ui.dashboard import render_dashboard

st.set_page_config(page_title="Radix Hackathon", layout="wide", page_icon="⚡")

def main():
    st.sidebar.title("Navegação")
    opcao = st.sidebar.radio("Ir para:", ["Dashboard Geral", "Análise de Imagem (IA)", "Sobre"])

    if opcao == "Dashboard Geral":
        render_dashboard()
    elif opcao == "Análise de Imagem (IA)":
        st.title("🚧 Em construção")
        st.info("Aqui entrará o código de reconhecimento de imagem do Google Maps + OpenCV")
    elif opcao == "Sobre":
        st.markdown("## Sobre o Projeto")
        st.markdown("Solução desenvolvida para o Hackathon Radix 2025.")

if __name__ == "__main__":
    main()