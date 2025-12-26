import requests
import pandas as pd
from functools import lru_cache

@lru_cache(maxsize=32)
def buscar_subestacoes_osm(cidade="Aracaju"):
    """
    Busca subestações no OpenStreetMap.
    Retorna DataFrame puro, sem dependência de interface.
    """
    query = f"""
    [out:json][timeout:15];
    area["name"="{cidade}"]->.searchArea;
    (
      node["power"="substation"](area.searchArea);
      way["power"="substation"](area.searchArea);
      rel["power"="substation"](area.searchArea);
    );
    out center;
    """

    try:
        response = requests.get(
            "https://overpass-api.de/api/interpreter",
            params={'data': query},
            headers={'User-Agent': 'RadixBot/1.0'},
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            subestacoes = []

            for el in data.get('elements', []):
                lat = el.get('lat') or el.get('center', {}).get('lat')
                lon = el.get('lon') or el.get('center', {}).get('lon')

                if lat and lon:
                    subestacoes.append({
                        'Nome': el.get('tags', {}).get('name', 'Subestação Sem Nome'),
                        'latitude': lat,
                        'longitude': lon,
                        'Tipo': 'Real'
                    })

            if subestacoes:
                return pd.DataFrame(subestacoes)

    except Exception as e:
        print(f"Erro OSM: {e}")

    # Fallback (se a API falhar, não quebra o backend)
    return pd.DataFrame()