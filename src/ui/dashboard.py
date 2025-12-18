import streamlit as st
import pandas as pd
import numpy as np
import cv2

from src.ui.components.styles import apply_custom_styles
from src.ui.components.sidebar import render_sidebar
from src.ui.map_view import render_map_component

from src.services.building_service import buscar_edificacoes_raio
from src.services.satellite_service import analisar_imagem_telhado, baixar_imagem_satelite
from src.utils.processing import gerar_grid_varredura


def testar_calibracao(img_pil, hsv_lower, hsv_upper):
    img = np.array(img_pil)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(hsv_lower), np.array(hsv_upper))
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask


def render_dashboard():
    apply_custom_styles()

    if 'map_center' not in st.session_state: st.session_state['map_center'] = [-10.9472, -37.0731]
    if 'map_zoom' not in st.session_state: st.session_state['map_zoom'] = 15
    if 'subestacoes' not in st.session_state: st.session_state['subestacoes'] = pd.DataFrame()
    if 'pontos_analise' not in st.session_state: st.session_state['pontos_analise'] = []
    if 'resultados_ia' not in st.session_state: st.session_state['resultados_ia'] = []

    modo_varredura, calib_params = render_sidebar()

    tab1, tab2 = st.tabs(["🗺️ Mapa & Scanner", "🧪 Laboratório de IA"])

    # --- ABA 1: MAPA ---
    with tab1:
        df_mapa = pd.DataFrame(st.session_state['pontos_analise']) if st.session_state['pontos_analise'] else None

        render_map_component(
            st.session_state['map_center'],
            st.session_state['map_zoom'],
            st.session_state['subestacoes'],
            df_mapa
        )

        df_subs = st.session_state['subestacoes']
        if not df_subs.empty:
            col1, col2 = st.columns([3, 1])
            escolha = col1.selectbox("Selecione Ativo:", df_subs['Nome'].unique())

            if col2.button("INICIAR SCAN", type="primary"):
                alvo = df_subs[df_subs['Nome'] == escolha].iloc[0]
                pontos = []

                if modo_varredura == "Edificações (OSM)":
                    with st.spinner("Buscando edificações..."):
                        df_casas = buscar_edificacoes_raio(alvo['latitude'], alvo['longitude'], raio_km=0.3)
                        for _, casa in df_casas.iterrows():
                            pontos.append({'latitude': casa['centro_lat'], 'longitude': casa['centro_lon'],
                                           'geometria': casa['geometria'], 'area': casa['area_m2']})
                else:
                    with st.spinner("Gerando grid..."):
                        grid = gerar_grid_varredura(alvo['latitude'], alvo['longitude'], raio_km=0.3, step_metros=50)
                        for pt in grid:
                            pt.update({'tipo': 'grid', 'area': 0})
                            pontos.append(pt)

                st.session_state['pontos_analise'] = pontos

                if pontos:
                    resultados = []
                    prog = st.progress(0)
                    amostra = pontos[:12]

                    for i, pt in enumerate(amostra):
                        img = baixar_imagem_satelite(pt['latitude'], pt['longitude'], size="600x600")
                        if img:
                            mask = testar_calibracao(img, calib_params[0], calib_params[1])
                            tem_gd = cv2.countNonZero(np.array(mask)) > 500
                            resultados.append({'img': img, 'mask': mask, 'lat': pt['latitude'], 'tem_gd': tem_gd})
                        prog.progress((i + 1) / len(amostra))

                    st.session_state['resultados_ia'] = resultados
                    st.rerun()

        if st.session_state['resultados_ia']:
            st.markdown("### 📸 Detecções")
            cols = st.columns(4)
            for i, res in enumerate(st.session_state['resultados_ia']):
                with cols[i % 4]:
                    st.image(res['img'], use_container_width=True)
                    if res['tem_gd']:
                        st.caption("✅ GD Detectada")

    # --- ABA 2: DEBUG ---
    with tab2:
        st.info("Ajuste os sliders na barra lateral e veja o efeito na máscara abaixo.")
        if st.session_state['resultados_ia']:
            sel = st.selectbox("Imagem", range(len(st.session_state['resultados_ia'])))
            item = st.session_state['resultados_ia'][sel]
            c1, c2 = st.columns(2)
            c1.image(item['img'], caption="Original")
            c2.image(item['mask'], caption="O que a IA vê")