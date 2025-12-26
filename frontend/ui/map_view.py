import folium
from streamlit_folium import st_folium


def render_map_component(center, zoom, subestacoes_df, pontos_df=None):
    # 1. Mapa Base (Google Satellite)
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        max_zoom=21,
        control_scale=True,
        tiles=None
    )

    # Camada Google Híbrida
    folium.TileLayer(
        tiles='http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=False,
        control=True,
        max_zoom=21
    ).add_to(m)

    # 2. Subestações (Ícones de Raio)
    if not subestacoes_df.empty:
        for _, row in subestacoes_df.iterrows():
            folium.Marker(
                [row['latitude'], row['longitude']],
                icon=folium.Icon(color="red", icon="bolt", prefix="fa"),
                tooltip=f"Sub: {row['Nome']}"
            ).add_to(m)

    # 3. Pontos de Análise (Casas ou Grid)
    if pontos_df is not None and not pontos_df.empty:
        for _, row in pontos_df.iterrows():

            # Garante que lê a área corretamente, independente do nome ou se é zero
            area_val = row.get('area', 0)

            # MODO 1: EDIFICAÇÕES (Tem desenho da casa)
            # Verifica se a coluna 'geometria' existe E se tem dados nela
            if 'geometria' in row and isinstance(row['geometria'], list) and len(row['geometria']) > 0:
                folium.Polygon(
                    locations=row['geometria'],
                    color="#00c0f2",
                    weight=2,
                    fill=True,
                    fill_opacity=0.1,
                    popup=f"Área: {area_val:.0f} m²"  # <--- AQUI ESTAVA O ERRO (Corrigido para usar area_val)
                ).add_to(m)

            # MODO 2: GRID (Força Bruta / Bolinhas)
            else:
                folium.CircleMarker(
                    location=[row['latitude'], row['longitude']],
                    radius=3,
                    color="#00c0f2",
                    fill=True,
                    fill_opacity=0.6,
                    popup="Ponto de Grid"
                ).add_to(m)

    return st_folium(m, width="100%", height=500)