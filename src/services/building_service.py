import requests
import pandas as pd
from shapely.geometry import Polygon
import numpy as np
import time


def buscar_edificacoes_raio(lat_centro, lon_centro, raio_km=0.3):
    # Lista de servidores para tentar (se um falhar, tenta o outro)
    servers = [
        "https://overpass-api.de/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
    ]

    raio_metros = raio_km * 1000
    query = f"""
    [out:json][timeout:25];
    (
      way["building"](around:{raio_metros},{lat_centro},{lon_centro});
    );
    out geom;
    """

    # Headers para não ser bloqueado (finge ser um browser)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.google.com/'
    }

    for server in servers:
        try:
            response = requests.get(server, params={'data': query}, headers=headers, timeout=30)

            # Se deu sucesso (200) e é JSON válido
            if response.status_code == 200:
                try:
                    data = response.json()
                    edificacoes = []

                    if 'elements' not in data:
                        return pd.DataFrame()

                    for element in data['elements']:
                        if 'geometry' in element:
                            coords = [(pt['lat'], pt['lon']) for pt in element['geometry']]
                            if len(coords) > 2:
                                poly = Polygon(coords)
                                # Estimativa de área
                                area_m2 = poly.area * 111132.95 * (111132.95 * np.cos(np.radians(lat_centro)))

                                edificacoes.append({
                                    'id': element['id'],
                                    'centro_lat': coords[0][0],
                                    'centro_lon': coords[0][1],
                                    'area_m2': abs(area_m2),
                                    'geometria': coords
                                })

                    return pd.DataFrame(edificacoes)

                except ValueError:
                    print(f"Erro JSON no servidor {server}. Tentando próximo...")
                    continue
            else:
                print(f"Erro {response.status_code} no servidor {server}")

        except Exception as e:
            print(f"Timeout ou erro de conexão no servidor {server}: {e}")
            time.sleep(1)  # Espera um pouco antes de tentar o próximo

    print("ERRO CRÍTICO: Não foi possível baixar edificações de nenhum servidor.")
    return pd.DataFrame()