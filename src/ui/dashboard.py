import streamlit as st
import pandas as pd
import numpy as np
import cv2

# Importações dos Componentes
from src.ui.components.styles import apply_custom_styles
from src.ui.components.sidebar import render_sidebar
from src.ui.map_view import render_map_component
from src.ui.components.result_view import render_results_view

# Serviços
from src.services.building_service import buscar_edificacoes_raio
from src.services.satellite_service import analisar_imagem_telhado, baixar_imagem_satelite

# NOVOS IMPORTS (Para H3 e Filtragem Espacial)
from src.utils.processing import gerar_malha_hexagonal
from src.services.osm_service import filtrar_pontos_em_ruas


# Função auxiliar para o Laboratório de IA (Debug visual rápido)
def testar_calibracao_debug(img_pil, hsv_lower, hsv_upper):
    img = np.array(img_pil)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(hsv_lower), np.array(hsv_upper))
    return mask


def render_dashboard():
    # 1. Aplica Estilos
    apply_custom_styles()

    # 2. Inicializa Estado
    if 'map_center' not in st.session_state: st.session_state['map_center'] = [-10.9472, -37.0731]
    if 'map_zoom' not in st.session_state: st.session_state['map_zoom'] = 15
    if 'subestacoes' not in st.session_state: st.session_state['subestacoes'] = pd.DataFrame()
    if 'pontos_analise' not in st.session_state: st.session_state['pontos_analise'] = []
    if 'resultados_ia' not in st.session_state: st.session_state['resultados_ia'] = []

    # 3. Renderiza Sidebar e pega parâmetros
    modo_varredura, calib_params = render_sidebar()

    # 4. Abas Principais
    tab1, tab2 = st.tabs(["🗺️ Mapa & Scanner", "🧪 Laboratório de IA"])

    # --- ABA 1: OPERAÇÃO ---
    with tab1:
        # Mapa
        df_mapa = pd.DataFrame(st.session_state['pontos_analise']) if st.session_state['pontos_analise'] else None

        render_map_component(
            st.session_state['map_center'],
            st.session_state['map_zoom'],
            st.session_state['subestacoes'],
            df_mapa
        )

        # Controles de Scan
        df_subs = st.session_state['subestacoes']
        if not df_subs.empty:
            col1, col2 = st.columns([3, 1])
            escolha = col1.selectbox("Selecione Ativo:", df_subs['Nome'].unique())

            if col2.button("INICIAR SCAN INTELIGENTE", type="primary"):
                alvo = df_subs[df_subs['Nome'] == escolha].iloc[0]
                pontos = []

                # --- ESTRATÉGIA DE BUSCA ---

                # MODO 1: Busca Exata (Se o OSM tiver os dados)
                if modo_varredura == "Edificações (OSM)":
                    with st.spinner("Buscando polígonos de edificações (OSM)..."):
                        df_casas = buscar_edificacoes_raio(alvo['latitude'], alvo['longitude'], raio_km=0.3)
                        for _, casa in df_casas.iterrows():
                            pontos.append({
                                'latitude': casa['centro_lat'],
                                'longitude': casa['centro_lon'],
                                'geometria': casa['geometria'],  # Desenha a casa exata
                                'area': casa['area_m2']
                            })

                # MODO 2: Busca Híbrida (H3 + Spatial Join)
                else:
                    st.toast("Iniciando Protocolo H3...")

                    # Passo A: Gerar Malha Hexagonal
                    with st.spinner("Gerando Malha Espacial H3 (Resolução 11)..."):
                        # Resolução 11 (~25m) é ideal para capturar lotes individuais
                        pontos_h3 = gerar_malha_hexagonal(alvo['latitude'], alvo['longitude'], raio_km=0.3,
                                                          resolucao=11)

                    # Passo B: Filtragem de Ruas (Spatial Join)
                    with st.spinner(f"Otimizando: Filtrando áreas públicas em {len(pontos_h3)} hexágonos..."):
                        pontos_filtrados = filtrar_pontos_em_ruas(pontos_h3)

                        removidos = len(pontos_h3) - len(pontos_filtrados)
                        if removidos > 0:
                            st.toast(f"📉 Otimização: {removidos} pontos em ruas foram removidos.")

                        # Padroniza para o mapa desenhar
                        for pt in pontos_filtrados:
                            # O H3 retorna 'geometria_hex', mas o mapa espera 'geometria'
                            pt['geometria'] = pt.get('geometria_hex')
                            pt['area'] = 0  # Grid não tem área real de telhado conhecida ainda
                            pontos.append(pt)

                st.session_state['pontos_analise'] = pontos

                # --- PROCESSAMENTO VISUAL ---
                if pontos:
                    resultados = []
                    prog = st.progress(0)

                    # Limite de segurança para demonstração (evitar travar a API do Google)
                    amostra = pontos[:20]

                    for i, pt in enumerate(amostra):
                        # Chama a IA (que agora aceita a calibração do slider)
                        img_final, ratio, tem_gd = analisar_imagem_telhado(
                            pt['latitude'],
                            pt['longitude'],
                            hsv_config=calib_params
                        )

                        if img_final:
                            resultados.append({
                                'img': img_final,
                                'lat': pt['latitude'],
                                'tem_gd': tem_gd
                            })
                        prog.progress((i + 1) / len(amostra))

                    st.session_state['resultados_ia'] = resultados
                    st.rerun()
                else:
                    st.warning("Nenhum ponto viável encontrado. Tente aumentar o raio ou mudar a área.")

        # Renderiza Relatório Final
        if st.session_state['resultados_ia']:
            render_results_view(st.session_state['resultados_ia'], raio_km=0.3)

    # --- ABA 2: LABORATÓRIO DE IA (CALIBRAÇÃO) ---
    with tab2:
        st.info("Ajuste os sliders laterais para 'ensinar' a IA a ver os painéis.")

        if st.session_state['resultados_ia']:
            sel_idx = st.selectbox("Selecione uma imagem:", range(len(st.session_state['resultados_ia'])))
            item = st.session_state['resultados_ia'][sel_idx]

            # Recalcula a máscara em tempo real usando os sliders atuais
            mask_debug = testar_calibracao_debug(item['img'], calib_params[0], calib_params[1])

            c1, c2 = st.columns(2)
            c1.image(item['img'], caption="Visão Humana (Original)", use_container_width=True)
            c2.image(mask_debug, caption="Visão da Máquina (Filtro)", use_container_width=True)

            st.markdown("""
            **Guia de Calibração:**
            * **Branco** = O que a IA detecta como Painel.
            * **Preto** = O que a IA ignora.
            * Ajuste até que o painel solar fique branco e o telhado/chão fiquem pretos.
            """)
        else:
            st.warning("Execute um Scan na primeira aba para carregar imagens aqui.")