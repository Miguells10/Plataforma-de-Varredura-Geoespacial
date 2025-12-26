import streamlit as st
import pandas as pd
import base64


def render_results(dados):
    """Exibe métricas, galeria de imagens e tabela de dados."""

    # 1. Título e KPIs
    st.divider()
    st.subheader(f"📊 Relatório: {dados['subestacao']}")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Imóveis Analisados", dados['total_analisado'])
    k2.metric("GDs Detectadas", dados['gds_encontradas'])

    # Cálculos Financeiros
    detalhes = dados.get('detalhes', [])
    potencia_total = sum([d['potencia'] for d in detalhes])
    receita_est = potencia_total * 5 * 30 * 0.85  # Ex: R$ 0,85/kWh

    k3.metric("Potência Oculta", f"{potencia_total:.2f} kW")
    k4.metric("Recuperação/Mês (Est.)", f"R$ {receita_est:,.2f}")

    if not detalhes:
        st.info("Nenhuma irregularidade encontrada.")
        return

    # 2. Abas de Visualização
    tab_img, tab_data = st.tabs(["📸 Evidências Visuais", "📋 Tabela Analítica"])

    with tab_img:
        cols = st.columns(4)
        for i, item in enumerate(detalhes):
            with cols[i % 4]:
                if item.get('imagem_base64'):
                    img_bytes = base64.b64decode(item['imagem_base64'])
                    st.image(img_bytes, use_container_width=True)
                    st.caption(f"**{item['classe']}** | {item['potencia']:.1f} kW")

    with tab_data:
        df = pd.DataFrame(detalhes)

        cols_desejadas = ['id', 'lat', 'lon', 'potencia', 'classe', 'tipo_osm']

        cols_finais = [c for c in cols_desejadas if c in df.columns]

        st.dataframe(
            df[cols_finais],
            use_container_width=True
        )