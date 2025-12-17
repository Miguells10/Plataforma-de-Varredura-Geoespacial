import requests
import pandas as pd
from shapely.geometry import Polygon
import numpy as np


def buscar_edificacoes_raio(lat_centro, lon_centro, raio_km=0.5):
    """
    Usa a API Overpass (OpenStreetMap) para buscar polígonos de prédios/casas
    dentro de um raio específico.
    """
    overpass_url = "http://overpass-api.de/api/interpreter"

    # Raio em metros
    raio_metros = raio_km * 1000

    # Query otimizada: Busca 'ways' (formas) que são 'building' (prédios)
    query = f"""
    [out:json][timeout:25];
    (
      way["building"](around:{raio_metros},{lat_centro},{lon_centro});
    );
    out geom;
    """

    try:
        response = requests.get(overpass_url, params={'data': query})
        data = response.json()

        edificacoes = []

        for element in data['elements']:
            if 'geometry' in element:
                # Reconstrói o polígono a partir dos pontos
                coords = [(pt['lat'], pt['lon']) for pt in element['geometry']]

                if len(coords) > 2:
                    poly = Polygon(coords)
                    # Cálculo geodésico simplificado de área (para latitudes do Brasil)
                    # 1 grau ~ 111km. Isso é uma aproximação para hackathon.
                    # Para precisão total usaria GeoPandas com projeção UTM, mas é pesado.
                    lat_factor = 111132.95
                    lon_factor = 111412.84 * np.cos(np.radians(lat_centro))

                    # Converte área de graus² para metros²
                    area_m2 = poly.area * lat_factor * lon_factor

                    edificacoes.append({
                        'id': element['id'],
                        'centro_lat': coords[0][0],  # Pega um ponto do telhado
                        'centro_lon': coords[0][1],
                        'area_m2': abs(area_m2),
                        'geometria': coords  # Guarda o desenho para o mapa
                    })

        return pd.DataFrame(edificacoes)

    except Exception as e:
        print(f"Erro ao buscar edificações: {e}")
        return pd.DataFrame()