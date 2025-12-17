import folium
from streamlit_folium import st_folium


def render_map_component(center, zoom, subestacoes_df, edificacoes_df=None):
    # 1. Configura o Mapa Base
    # max_zoom=21 permite chegar BEM perto sem ficar cinza
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        max_zoom=21,
        control_scale=True,
        tiles=None  # Vamos adicionar o tile manualmente abaixo
    )

    # 2. ADICIONA O GOOGLE SATELLITE (HÍBRIDO)
    # Essa URL é a mesma usada pelo Google Maps no navegador
    folium.TileLayer(
        tiles='http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=False,
        control=True,
        max_zoom=21  # Garante que não trava no zoom
    ).add_to(m)

    # 3. Marcadores de Subestação
    if not subestacoes_df.empty:
        for _, row in subestacoes_df.iterrows():
            folium.Marker(
                [row['latitude'], row['longitude']],
                icon=folium.Icon(color="red", icon="bolt", prefix="fa"),
                tooltip=f"Sub: {row['Nome']}"
            ).add_to(m)

    # 4. Polígonos das Casas (OSM)
    if edificacoes_df is not None and not edificacoes_df.empty:
        for _, row in edificacoes_df.iterrows():
            # Desenha o contorno da casa
            folium.Polygon(
                locations=row['geometria'],
                color="#00c0f2",  # Borda Ciano
                weight=2,
                fill=True,
                fill_color="#00c0f2",
                fill_opacity=0.1,  # Bem transparente para ver o telhado embaixo
                popup=f"Área: {row['area_m2']:.0f} m²"
            ).add_to(m)

    return st_folium(m, width="100%", height=500)