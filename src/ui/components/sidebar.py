import streamlit as st
from src.services.osm_service import buscar_subestacoes_osm


def render_sidebar():
    with st.sidebar:
        st.header("RADIX | Controle")

        # Opções
        modo = st.radio("Modo de Varredura", ["Edificações (OSM)", "Grid Inteligente (H3)"])
        st.info("💡 Use 'Grid Inteligente' se o mapa não tiver casas desenhadas.")

        cidade = st.text_input("Cidade", "Aracaju")

        # Botão de Busca
        if st.button("📍 Buscar Subestação", use_container_width=True):
            with st.spinner("Conectando..."):
                try:
                    df = buscar_subestacoes_osm(cidade)

                    # VERIFICAÇÃO DE SEGURANÇA (Onde estava dando erro)
                    if df is not None and not df.empty:
                        st.session_state['subestacoes'] = df
                        # Centraliza na primeira
                        lat = df.iloc[0]['latitude']
                        lon = df.iloc[0]['longitude']
                        st.session_state['map_center'] = [lat, lon]
                        st.success(f"{len(df)} ativos carregados.")
                        st.rerun()
                    else:
                        st.error("Nenhuma subestação encontrada. Tente 'Aracaju' para ver o Demo.")
                except Exception as e:
                    st.error(f"Erro ao processar dados: {e}")

        st.markdown("---")

        # Calibração
        st.header("🔧 Calibrar IA")
        with st.expander("Ajuste Fino (Cor)", expanded=True):
            h_min = st.slider("Hue Min", 0, 179, 90)
            h_max = st.slider("Hue Max", 0, 179, 140)
            s_min = st.slider("Sat Min", 0, 255, 30)
            v_min = st.slider("Val Min", 0, 255, 40)

        return modo, ([h_min, s_min, v_min], [h_max, 255, 255])