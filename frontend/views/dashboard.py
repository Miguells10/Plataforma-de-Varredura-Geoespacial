import streamlit as st
import pandas as pd
import base64
from streamlit_folium import st_folium
from frontend.core.api_client import RadixAPI
from frontend.components.map_display import render_map


def render_dashboard_view(df_subs):
    # Memória do Scan
    if 'scan_data' not in st.session_state:
        st.session_state['scan_data'] = None

    # --- BARRA LATERAL (CONTROLES) ---
    with st.sidebar:
        st.header("🎮 Centro de Controle")

        # Seleção de Ativo
        opcoes = df_subs['Nome'].unique()
        escolha = st.selectbox("Subestação Alvo", opcoes)
        alvo = df_subs[df_subs['Nome'] == escolha].iloc[0]

        st.divider()

        # Parâmetros
        with st.expander("📡 Configuração do Radar", expanded=True):
            modo = st.radio("Modo de Varredura", ["Edificações (OSM)", "Grid (Rural/Falhas)"])
            modo_code = "grid" if "Grid" in modo else "osm"

            raio = st.slider("Raio (km)", 0.2, 2.0, 0.5)
            voronoi = st.checkbox("Filtro Voronoi", value=True)

        st.info(f"📍 Alvo: {escolha}\n\n🌐 Lat: {alvo['latitude']:.4f}\n🌐 Lon: {alvo['longitude']:.4f}")

        # Botão de Ação
        btn_scan = st.button("🚀 INICIAR VARREDURA", type="primary", use_container_width=True)

    # --- LÓGICA DE EXECUÇÃO ---
    if btn_scan:
        payload = {
            "subestacao_nome": alvo['Nome'],
            "latitude": float(alvo['latitude']),
            "longitude": float(alvo['longitude']),
            "raio_km": raio,
            "usar_voronoi": voronoi,
            "modo": modo_code
        }

        with st.spinner("🛰️ Satélite posicionando... Processando imagens com IA..."):
            resultado = RadixAPI.executar_scan(payload)
            if resultado:
                st.session_state['scan_data'] = resultado
            else:
                st.error("Sem resposta do satélite (API).")

    # --- LAYOUT PRINCIPAL (ABAS) ---
    # Aqui recuperamos a usabilidade que você gostava
    tab_mapa, tab_lab = st.tabs(["🗺️ Mapa Tático", "🔬 Laboratório de IA"])

    # ABA 1: MAPA
    with tab_mapa:
        pontos = []
        if st.session_state['scan_data']:
            pontos = st.session_state['scan_data']['detalhes']

            # KPIs Rápidos no topo do mapa
            k1, k2, k3 = st.columns(3)
            k1.metric("Pontos Varridos", st.session_state['scan_data']['total_analisado'])
            k2.metric("GDs Encontradas", st.session_state['scan_data']['gds_encontradas'])
            pot_total = sum([d['potencia'] for d in pontos])
            k3.metric("Potência (kW)", f"{pot_total:.2f}")

        # Renderiza Mapa (Google Hybrid)
        mapa_obj = render_map(df_subs, destaque=alvo, pontos_scan=pontos)
        st_folium(mapa_obj, width="100%", height=600, returned_objects=[])

    # ABA 2: LABORATÓRIO (A Galeria Interativa)
    with tab_lab:
        if not st.session_state['scan_data']:
            st.info("⚠️ Execute uma varredura para habilitar o laboratório.")
        else:
            resultados = st.session_state['scan_data']['detalhes']

            if not resultados:
                st.warning("Nenhum alvo detectado.")
            else:
                st.subheader("Análise Detalhada de Evidências")

                # Seletor de Imagem (Como era antes!)
                opcoes_img = [f"ID: {r['id']} | {r['classe']} ({r['potencia']} kW)" for r in resultados]
                escolha_img = st.selectbox("Selecione um alvo para inspeção:", opcoes_img)

                # Pega o índice
                idx = opcoes_img.index(escolha_img)
                dado = resultados[idx]

                # Layout de Inspeção
                c_img, c_info = st.columns([1, 1])

                with c_img:
                    if dado.get('imagem_base64'):
                        img_bytes = base64.b64decode(dado['imagem_base64'])
                        st.image(img_bytes, caption="Visão Computacional (YOLOv8)", use_container_width=True)

                with c_info:
                    st.markdown(f"### 📋 Dossiê do Alvo")
                    st.write(f"**ID:** `{dado['id']}`")
                    st.write(f"**Coordenadas:** {dado['lat']:.5f}, {dado['lon']:.5f}")
                    st.write(f"**Classificação OSM:** {dado.get('tipo_osm', 'N/A')}")

                    st.divider()

                    if dado['potencia'] > 0:
                        st.success(f"✅ **GD CONFIRMADA**")
                        st.metric("Potência Estimada", f"{dado['potencia']} kW")
                        st.caption("Baseado na área de painéis detectada.")
                    else:
                        st.warning("🔸 Nenhuma GD detectada")

                    st.markdown("---")
                    st.markdown("**Diagnóstico da IA:**")
                    st.text(
                        "O modelo identificou padrões retangulares\ncompatíveis com módulos fotovoltaicos\ne alto contraste térmico/visual.")