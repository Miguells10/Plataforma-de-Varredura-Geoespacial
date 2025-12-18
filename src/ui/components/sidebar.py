import streamlit as st
import pandas as pd
from src.services.osm_service import buscar_subestacoes_osm


def render_sidebar():
    with st.sidebar:
        st.header("RADIX | Controle")

        # 1. Configurações de Busca
        modo = st.radio("Modo de Varredura", ["Edificações (OSM)", "Grid (Força Bruta)"])
        st.info("💡 'Grid' ignora o mapa e varre tudo.")

        cidade = st.text_input("Cidade", "Aracaju")

        if st.button("📍 Buscar Subestação", use_container_width=True):
            with st.spinner("Consultando OSM..."):
                df = buscar_subestacoes_osm(cidade)
                if not df.empty:
                    st.session_state['subestacoes'] = df
                    # Centraliza o mapa na primeira subestação achada
                    st.session_state['map_center'] = [df.iloc[0]['latitude'], df.iloc[0]['longitude']]
                    st.success(f"{len(df)} ativos encontrados.")
                    st.rerun()
                else:
                    st.error("Cidade não encontrada.")

        st.markdown("---")

        # 2. Calibração da IA
        st.header("🔧 Calibrar IA")
        with st.expander("Ajuste Fino de Detecção", expanded=True):
            st.caption("Intervalo de Cor (HSV)")
            h_min = st.slider("Hue Min", 0, 179, 90)
            h_max = st.slider("Hue Max", 0, 179, 140)
            s_min = st.slider("Sat Min", 0, 255, 30)
            v_min = st.slider("Val Min", 0, 255, 40)

        # Retorna os parâmetros para quem chamar a função usar
        return modo, ([h_min, s_min, v_min], [h_max, 255, 255])