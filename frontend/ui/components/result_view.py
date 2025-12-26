import streamlit as st
import pandas as pd


def render_results_view(results_ia, raio_km):
    """
    Renderiza o painel de resultados: Métricas, Gráficos e Galeria de Imagens.
    Recebe:
        - results_ia: Lista de dicionários com as imagens processadas e flags de detecção.
        - raio_km: O raio utilizado no scan (para cálculo de área).
    """

    if not results_ia:
        return

    st.markdown("---")
    st.header("📊 Relatório de Inteligência Geoespacial")

    total_analisado = len(results_ia)
    gds_detectadas = sum(1 for r in results_ia if r.get('tem_gd', False))

    soma_potencia_kw = sum(r.get('potencia_kw', 0) for r in results_ia)
    potencia_estimada_mw = soma_potencia_kw / 1000.0

    capacidade_subestacao = 5.0
    penetracao_gd = (potencia_estimada_mw / capacidade_subestacao) * 100

    # --- 2. CARDS DE MÉTRICAS (KPIs) ---
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Pontos Analisados</div>
            <div class="metric-value">{total_analisado}</div>
            <div style="font-size: 12px; color: #aaa;">Amostra Visual</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        alerta_class = "alert" if penetracao_gd > 15 else ""
        cor_valor = "#ff4b4b" if penetracao_gd > 15 else "#00c0f2"

        st.markdown(f"""
        <div class="metric-card {alerta_class}">
            <div class="metric-label">GDs Detectadas (IA)</div>
            <div class="metric-value" style="color: {cor_valor};">{gds_detectadas}</div>
            <div style="font-size: 12px; color: #aaa;">Unidades Confirmadas</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Potência Oculta Est.</div>
            <div class="metric-value">{potencia_estimada_mw:.3f} MW</div>
            <div style="font-size: 12px; color: #aaa;">~{penetracao_gd:.1f}% da Subestação</div>
        </div>
        """, unsafe_allow_html=True)

    # --- 3. GRÁFICO E DOWNLOAD ---
    c_chart, c_down = st.columns([2, 1])

    with c_chart:
        st.caption("⚖️ Balanço de Carga Estimado")
        chart_data = pd.DataFrame({
            "Componente": ["Capacidade Nominal", "Carga Base (Sem GD)", "Geração Distribuída (Radix)"],
            "Potência (MW)": [capacidade_subestacao, 3.5, potencia_estimada_mw],
            "Cor": ["#333333", "#1f77b4", "#00c0f2"]
        })
        st.bar_chart(chart_data, x="Componente", y="Potência (MW)", color="Cor", use_container_width=True)

    with c_down:
        st.write("")
        st.write("")
        st.info("📥 Exporte os dados para integração com sistema legado.")

        df_export = pd.DataFrame(results_ia)
        cols_to_keep = [k for k in df_export.columns if k not in ['img', 'mask']]
        csv = df_export[cols_to_keep].to_csv(index=False).encode('utf-8')

        st.download_button(
            label="Baixar Relatório (CSV)",
            data=csv,
            file_name="relatorio_radix_scan.csv",
            mime="text/csv",
            use_container_width=True
        )
    st.markdown("### 📸 Evidências Visuais")
    st.caption("Imagens processadas pelo algoritmo de Visão Computacional (Verde = Detecção Positiva)")

    cols = st.columns(4)
    for i, res in enumerate(results_ia):
        with cols[i % 4]:
            st.image(res['img'], use_container_width=True)

            if res.get('tem_gd'):
                st.markdown(":white_check_mark: :green[**GD Confirmada**]")
            else:
                st.markdown(":small_blue_diamond: :grey[Sem Painel]")

            st.caption(f"Lat: {res.get('lat', 0):.5f}")