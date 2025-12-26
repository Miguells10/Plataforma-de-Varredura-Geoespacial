import folium
from streamlit_folium import st_folium


def render_map(df_subs, destaque=None, pontos_scan=None):
    """
    Gera o mapa com tiles do Google Satellite (Híbrido) e desenha os resultados do scan.
    """
    # Centro e Zoom
    centro = [-10.9472, -37.0731]
    zoom = 13

    if destaque is not None:
        centro = [float(destaque['latitude']), float(destaque['longitude'])]
        zoom = 16

    # 1. Mapa Base (Google Hybrid - O melhor para ver telhados)
    m = folium.Map(
        location=centro,
        zoom_start=zoom,
        tiles=None,  # Remove o padrão para usar o do Google
        control_scale=True
    )

    folium.TileLayer(
        tiles='http://mt0.google.com/vt/lyrs=y&hl=pt-br&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=False,
        control=True,
        max_zoom=21
    ).add_to(m)

    # 2. Marcadores das Subestações
    if not df_subs.empty:
        for _, row in df_subs.iterrows():
            folium.Marker(
                [row['latitude'], row['longitude']],
                tooltip=f"SE {row['Nome']}",
                icon=folium.Icon(color="red", icon="bolt", prefix="fa")
            ).add_to(m)

            # Raio de Destaque
            if destaque is not None and row['Nome'] == destaque['Nome']:
                folium.Circle(
                    location=[row['latitude'], row['longitude']],
                    radius=500,  # Visual apenas
                    color="#00c0f2",
                    weight=1,
                    fill=False
                ).add_to(m)

    # 3. Resultados do Scan (Casas ou Grid)
    if pontos_scan:
        for pt in pontos_scan:
            lat, lon = pt['lat'], pt['lon']
            cor = "#00ff00" if pt.get('tem_gd') else "#00c0f2"
            fill_cor = "#00ff00" if pt.get('tem_gd') else "#00c0f2"

            # Se for EDIFICAÇÃO (tem geometria desenhada)
            # Nota: O backend precisa passar 'geometria' se quisermos desenhar o polígono.
            # Se não tiver geometria, usamos CircleMarker como fallback elegante.
            folium.CircleMarker(
                location=[lat, lon],
                radius=4,
                color=cor,
                weight=1,
                fill=True,
                fill_color=fill_cor,
                fill_opacity=0.7,
                popup=f"Potência: {pt.get('potencia', 0)} kW"
            ).add_to(m)

    return m