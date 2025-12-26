import streamlit as st
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from frontend.core.settings import APP_TITLE, APP_ICON, apply_custom_css
from frontend.core.api_client import RadixAPI
from frontend.views.dashboard import render_dashboard_view

st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")
apply_custom_css()


def main():
    st.title(APP_TITLE)
    st.caption("Enterprise Asset Management & Loss Detection System")

    with st.sidebar:
        st.header("Conexão")
        if RadixAPI.check_health():
            st.success("Backend Online")
        else:
            st.error("Backend Offline")
            st.stop()

        cidade = st.text_input("Cidade", "Aracaju")
        if st.button("Carregar Rede"):
            st.session_state['subs'] = RadixAPI.get_subestacoes(cidade)
            st.rerun()

    if 'subs' in st.session_state and not st.session_state['subs'].empty:
        render_dashboard_view(st.session_state['subs'])
    else:
        st.info("Aguardando carregamento da rede elétrica. Utilize a barra lateral.")


if __name__ == "__main__":
    main()