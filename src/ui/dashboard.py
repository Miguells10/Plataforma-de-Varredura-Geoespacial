import streamlit as st
import pandas as pd
import time
import cv2
import numpy as np
from PIL import Image

# Importações
from src.services.osm_service import buscar_subestacoes_osm
from src.services.building_service import buscar_edificacoes_raio
from src.services.satellite_service import analisar_imagem_telhado, baixar_imagem_satelite
from src.utils.processing import gerar_grid_varredura  # Traz de volta o Grid
from src.ui.map_view import render_map_component


# --- FUNÇÃO DE CALIBRAÇÃO (Nova) ---
def testar_calibracao(img_pil, hsv_lower, hsv_upper):
    """Roda a detecção numa imagem única com os valores dos sliders"""
    img = np.array(img_pil)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Cria a máscara com os valores do slider
    mask = cv2.inRange(hsv, np.array(hsv_lower), np.array(hsv_upper))

    # Limpeza visual
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Desenha contornos na imagem original
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    img_result = img.copy()
    cv2.drawContours(img_result, contours, -1, (0, 255, 0), 2)

    return Image.fromarray(cv2.cvtColor(img_result, cv2.COLOR_BGR2RGB)), Image.fromarray(mask)


def render_dashboard():
    st.markdown("""
        <style>
        .metric-card { background-color: #0E1117; border: 1px solid #333; border-left: 5px solid #00c0f2; padding: 15px; border-radius: 8px; color: white; margin-bottom: 10px; }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #0E1117; border-radius: 5px; }
        </style>
    """, unsafe_allow_html=True)

    # Inicialização
    if 'map_center' not in st.session_state: st.session_state['map_center'] = [-10.9472, -37.0731]
    if 'map_zoom' not in st.session_state: st.session_state['map_zoom'] = 15
    if 'subestacoes' not in st.session_state: st.session_state['subestacoes'] = pd.DataFrame()
    if 'pontos_analise' not in st.session_state: st.session_state['pontos_analise'] = []  # Unifica casas e grid
    if 'resultados_ia' not in st.session_state: st.session_state['resultados_ia'] = []

    # --- BARRA LATERAL ---
    with st.sidebar:
        st.header("RADIX | Controle")

        modo_varredura = st.radio("Modo de Varredura", ["Edificações (OSM)", "Grid (Força Bruta)"])
        st.info("💡 Use 'Grid' se o mapa não mostrar as casas do condomínio.")

        cidade = st.text_input("Cidade", "Aracaju")
        if st.button("Buscar Subestação"):
            df = buscar_subestacoes_osm(cidade)
            if not df.empty:
                st.session_state['subestacoes'] = df
                st.session_state['map_center'] = [df.iloc[0]['latitude'], df.iloc[0]['longitude']]
                st.rerun()

        st.markdown("---")
        st.header("🔧 Calibrar IA")
        st.write("Ajuste a cor para detectar as placas:")

        # SLIDERS DE CALIBRAÇÃO HSV
        h_min = st.slider("Hue Min (Cor)", 0, 179, 90)
        h_max = st.slider("Hue Max (Cor)", 0, 179, 140)
        s_min = st.slider("Sat Min (Vibrante)", 0, 255, 30)
        v_min = st.slider("Val Min (Brilho)", 0, 255, 40)

        calib_params = ([h_min, s_min, v_min], [h_max, 255, 255])

    # --- ÁREA PRINCIPAL ---
    tab1, tab2 = st.tabs(["🗺️ Mapa & Scanner", "🧪 Laboratório de IA (Debug)"])

    with tab1:
        st.subheader("Varredura Geoespacial")

        # Mapa
        render_map_component(
            st.session_state['map_center'],
            st.session_state['map_zoom'],
            st.session_state['subestacoes'],
            # Se for modo Edificações, passa o DF, se for Grid, passa os pontos
            pd.DataFrame(st.session_state['pontos_analise']) if modo_varredura == "Edificações (OSM)" else None
        )

        df_subs = st.session_state['subestacoes']
        if not df_subs.empty:
            col1, col2 = st.columns([3, 1])
            escolha = col1.selectbox("Selecione Ativo:", df_subs['Nome'].unique())

            if col2.button("SCANEAR", type="primary", use_container_width=True):
                alvo = df_subs[df_subs['Nome'] == escolha].iloc[0]

                pontos = []
                # ESTRATÉGIA HÍBRIDA
                if modo_varredura == "Edificações (OSM)":
                    with st.spinner("Buscando casas no mapa..."):
                        df_casas = buscar_edificacoes_raio(alvo['latitude'], alvo['longitude'], raio_km=0.3)
                        # Converte formato OSM para formato genérico de pontos
                        for _, casa in df_casas.iterrows():
                            pontos.append(
                                {'latitude': casa['centro_lat'], 'longitude': casa['centro_lon'], 'tipo': 'casa',
                                 'area': casa['area_m2']})
                else:
                    with st.spinner("Gerando grid geoespacial..."):
                        # Grid de 50 em 50 metros
                        grid = gerar_grid_varredura(alvo['latitude'], alvo['longitude'], raio_km=0.3, step_metros=50)
                        for pt in grid:
                            pt['tipo'] = 'grid'
                            pt['area'] = 0
                            pontos.append(pt)

                st.session_state['pontos_analise'] = pontos

                if not pontos:
                    st.error("Nada encontrado. Tente mudar para 'Grid' ou aumentar o raio.")
                else:
                    # RODA ANÁLISE (Limitado a 12 para não travar)
                    resultados = []
                    prog = st.progress(0)
                    status = st.empty()

                    amostra = pontos[:12]  # Pega os 12 primeiros pontos/casas

                    for i, pt in enumerate(amostra):
                        status.text(f"Analisando ponto {i + 1}/{len(amostra)}...")

                        # Usa a função de serviço, MAS vamos injetar a calibração manual
                        # Para facilitar, vou chamar a função de baixar imagem e rodar a calibração aqui
                        img = baixar_imagem_satelite(pt['latitude'], pt['longitude'], size="600x600")  # Imagem limpa

                        if img:
                            # Aplica a calibração atual dos sliders
                            img_res, mask = testar_calibracao(img[0] if isinstance(img, tuple) else img,
                                                              calib_params[0], calib_params[1])

                            # Verifica se achou algo branco na máscara (pixels > 0)
                            mask_arr = np.array(mask)
                            pixels = cv2.countNonZero(mask_arr)
                            tem_gd = pixels > 500  # Sensibilidade

                            resultados.append({
                                'img': img_res,
                                'mask': mask,
                                'lat': pt['latitude'],
                                'tem_gd': tem_gd
                            })

                        prog.progress((i + 1) / len(amostra))

                    st.session_state['resultados_ia'] = resultados
                    st.rerun()

        # RESULTADOS
        if st.session_state['resultados_ia']:
            st.markdown("### Resultados Detectados")
            cols = st.columns(4)
            for i, res in enumerate(st.session_state['resultados_ia']):
                with cols[i % 4]:
                    st.image(res['img'], caption=f"Lat: {res['lat']:.5f}", use_container_width=True)
                    if res['tem_gd']:
                        st.markdown(":white_check_mark: :green[**GD Confirmada**]")
                    else:
                        st.caption("Sem detecção")

    with tab2:
        st.subheader("🔧 Debug da Visão Computacional")
        st.write("Use esta aba para entender O QUE a IA está enxergando.")

        if st.session_state['resultados_ia']:
            sel_res = st.selectbox("Selecione uma imagem analisada:", range(len(st.session_state['resultados_ia'])))
            item = st.session_state['resultados_ia'][sel_res]

            c1, c2 = st.columns(2)
            with c1:
                st.image(item['img'], caption="Imagem Processada (Com Contornos)", use_container_width=True)
            with c2:
                st.image(item['mask'], caption="Máscara (O que a IA filtrou)", use_container_width=True)

            st.warning(
                "Se a Máscara estiver toda preta, ajuste os Sliders na barra lateral (Hue/Sat/Val) até aparecerem manchas brancas onde estão as placas.")
            st.info("Dica: Placas azuis costumam ter Hue entre 90-140. Placas pretas, Hue 0-180 mas Sat baixo.")