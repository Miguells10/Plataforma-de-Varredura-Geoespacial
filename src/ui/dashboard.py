import streamlit as st
import pandas as pd
import time

from src.ui.components.sidebar import render_sidebar
from src.ui.map_view import render_map_component
from src.ui.components.result_view import render_results_view
from src.ui.components.styles import apply_custom_styles

from src.services.building_service import buscar_edificacoes_raio
from src.utils.processing import prepare_scan_data
from src.services.satellite_service import analisar_imagem_telhado


def render_dashboard():
    # 1. Configuração Inicial
    apply_custom_styles()

    if 'map_center' not in st.session_state: st.session_state['map_center'] = [-10.9472, -37.0731]
    if 'pontos_analise' not in st.session_state: st.session_state['pontos_analise'] = []
    if 'resultados_ia' not in st.session_state: st.session_state['resultados_ia'] = []
    if 'subestacoes' not in st.session_state: st.session_state['subestacoes'] = pd.DataFrame()

    modo_varredura, calib_params = render_sidebar()

    # 3. Layout Principal
    tab1, tab2 = st.tabs(["🗺️ Operação & Mapa", "⚙️ Laboratório IA"])

    with tab1:
        # Mapa
        df_mapa = pd.DataFrame(st.session_state['pontos_analise']) if st.session_state['pontos_analise'] else None
        render_map_component(
            st.session_state['map_center'],
            16,
            st.session_state['subestacoes'],
            df_mapa
        )

        # Controles de Scan
        df_subs = st.session_state['subestacoes']
        if not df_subs.empty:
            st.divider()
            col1, col2 = st.columns([3, 1])
            escolha = col1.selectbox("Selecione o Ativo:", df_subs['Nome'].unique())

            if col2.button("INICIAR SCAN", type="primary", use_container_width=True):
                # Pega coordenada do alvo
                alvo = df_subs[df_subs['Nome'] == escolha].iloc[0]
                lat_alvo, lon_alvo = alvo['latitude'], alvo['longitude']

                # --- PASSO 1: Busca Edificações (Ou Mock) ---
                casas_df = pd.DataFrame()
                if modo_varredura == "Edificações (OSM)":
                    with st.spinner("Obtendo dados de edificações..."):
                        casas_df = buscar_edificacoes_raio(lat_alvo, lon_alvo, radius_km=0.3)

                with st.spinner("Calculando malha de varredura..."):
                    lista_casas = casas_df.to_dict('records') if not casas_df.empty else []

                    points = prepare_scan_data(
                        lat_alvo, lon_alvo,
                        buildings=lista_casas,
                        radius_km=0.3,
                        use_buildings=(modo_varredura == "Edificações (OSM)")
                    )

                st.session_state['pontos_analise'] = points

                if points:
                    resultados = []
                    progresso = st.progress(0)
                    status = st.empty()

                    amostra = points[:20]

                    for i, pt in enumerate(amostra):
                        status.text(f"Analisando alvo {i + 1}/{len(amostra)}...")

                        img, ratio, tem_gd = analisar_imagem_telhado(
                            pt['latitude'],
                            pt['longitude'],
                            hsv_config=calib_params
                        )

                        if img:
                            resultados.append({
                                'img': img,
                                'lat': pt['latitude'],
                                'tem_gd': tem_gd
                            })

                        progresso.progress((i + 1) / len(amostra))
                        time.sleep(0.1)

                    st.session_state['resultados_ia'] = resultados
                    st.success("Varredura Completa!")
                    st.rerun()
                else:
                    st.error("Nenhum ponto gerado para varredura.")

        # Resultados
        if st.session_state['resultados_ia']:
            render_results_view(st.session_state['resultados_ia'], raio_km=0.3)

    with tab2:
        st.header("🔬 Laboratório de Visão Computacional")

        if st.session_state['resultados_ia']:

            opcoes_img = [f"Imagem {i + 1} (Lat: {r['lat']:.5f})" for i, r in
                          enumerate(st.session_state['resultados_ia'])]
            escolha = st.selectbox("Selecione uma imagem do Scan:", options=opcoes_img)

            # Pega o índice da escolha
            idx = opcoes_img.index(escolha)
            dados_escolhidos = st.session_state['resultados_ia'][idx]

            # Mostra a imagem
            col_a, col_b = st.columns(2)
            with col_a:
                st.image(dados_escolhidos['img'], caption="Imagem Processada pela IA", use_container_width=True)

            with col_b:
                st.info("Status da Detecção:")
                if dados_escolhidos['tem_gd']:
                    st.success("✅ GD Detectada (Textura de Painel encontrada)")
                else:
                    st.warning("🔸 Nenhuma GD confirmada (Área lisa ou formato irregular)")

                st.markdown("**Por que a IA decidiu isso?**")
                st.text(
                    "O algoritmo analisou:\n1. Formato (Retangular)\n2. Textura (Linhas internas)\n3. Contraste (Escuro vs Claro)")

        else:
            st.info("⚠️ O Laboratório está vazio.")
            st.markdown("""
            **Como usar:**
            1. Vá na aba 'Operação & Mapa'.
            2. Selecione uma subestação.
            3. Clique em **INICIAR SCAN**.
            4. Espere o processamento terminar.
            5. Volte aqui para analisar os resultados detalhados.
            """)