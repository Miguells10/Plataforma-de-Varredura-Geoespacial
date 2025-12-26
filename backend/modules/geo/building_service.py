import requests
import pandas as pd
import random


def buscar_edificacoes_raio(lat, lon, radius_km=0.5):
    """
    Busca edificações (polígonos) ao redor de uma coordenada.
    """
    query = f"""
    [out:json][timeout:10];
    way["building"](around:{radius_km * 1000},{lat},{lon});
    out center tags;
    """
    try:
        resp = requests.get("https://overpass-api.de/api/interpreter", params={'data': query}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            buildings = []

            for el in data.get('elements', []):
                if 'center' in el:
                    tags = el.get('tags', {})
                    tipo = tags.get('building', 'yes')

                    # Classificação simples baseada em tags OSM
                    cat = "Desconhecido"
                    if tipo in ['industrial', 'commercial', 'retail']:
                        cat = "Comercial/Ind"
                    elif tipo in ['house', 'residential', 'apartments']:
                        cat = "Residencial"

                    buildings.append({
                        'id': el['id'],
                        'centro_lat': el['center']['lat'],
                        'centro_lon': el['center']['lon'],
                        'categoria_osm': cat,
                        'geometria': []  # Geometria complexa removida para leveza
                    })

            if buildings:
                return pd.DataFrame(buildings)

    except Exception as e:
        print(f"Erro Building Service: {e}")

    return pd.DataFrame()  # Retorna vazio em vez de Mock para produção