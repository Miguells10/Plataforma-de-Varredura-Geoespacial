import h3
import geopandas as gpd
from shapely.geometry import Point, Polygon, box
import pandas as pd
import numpy as np


def gerar_malha_hexagonal(lat_centro, lon_centro, raio_km=0.5, resolucao=10):
    """
    Gera uma malha H3 (Hexágonos) circular ao redor de um ponto.
    Resolução 10 = Hexágonos de ~66m de lado (ideal para quarteirões/lotes).
    Resolução 11 = Hexágonos de ~25m (ideal para casas individuais).
    """
    # 1. Cria um Buffer Circular usando GeoPandas (mais preciso que conta de padaria)
    # Criamos um ponto e projetamos para metros (EPSG:3857) para fazer o buffer em Km
    df_ponto = gpd.GeoDataFrame(geometry=[Point(lon_centro, lat_centro)], crs="EPSG:4326")
    df_metro = df_ponto.to_crs(epsg=3857)

    # Gera o circulo (raio em metros)
    buffer_metro = df_metro.buffer(raio_km * 1000)

    # Volta para Lat/Lon (O H3 precisa disso)
    buffer_geo = buffer_metro.to_crs(epsg=4326).iloc[0]

    # 2. Preenche o polígono com Hexágonos (Polyfill)
    # A lib h3 precisa do formato GeoJSON {type: Polygon, coordinates: [...]}
    mapping = buffer_geo.__geo_interface__

    # O H3 trabalha com coordenadas (lat, lon), o GeoJSON é (lon, lat). Precisamos inverter se necessário.
    # Mas a lib 'h3' moderna aceita bem. Vamos usar a função 'polyfill_geojson'
    hexagons = h3.polyfill(mapping, res=resolucao, geo_json_conformant=True)

    # 3. Extrai os Centroides para buscar a imagem
    pontos_analise = []
    for hex_id in hexagons:
        lat, lon = h3.h3_to_geo(hex_id)
        pontos_analise.append({
            'id': hex_id,
            'latitude': lat,
            'longitude': lon,
            'tipo': 'h3_hex',
            'geometria_hex': h3.h3_to_geo_boundary(hex_id, geo_json=True)  # Para desenhar no mapa
        })

    return pontos_analise