import requests
import random
import pandas as pd


def _mock_buildings(lat, lon, count=20):
    """Gera casas falsas para demo."""
    mocks = []
    for i in range(count):
        d_lat = random.uniform(-0.003, 0.003)
        d_lon = random.uniform(-0.003, 0.003)
        mocks.append({
            'id': f'mock_{i}',
            'centro_lat': lat + d_lat,
            'centro_lon': lon + d_lon,
            'geometria': [],
            'area_m2': random.randint(100, 300)
        })
    return pd.DataFrame(mocks)


def buscar_edificacoes_raio(lat, lon, radius_km=0.5):
    """Busca edificações no OSM com fallback para Mock."""
    query = f"""
    [out:json][timeout:5];
    way["building"](around:{radius_km * 1000},{lat},{lon});
    out center;
    """
    try:
        resp = requests.get("https://overpass-api.de/api/interpreter", params={'data': query}, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            buildings = []
            for el in data.get('elements', []):
                if 'center' in el:
                    buildings.append({
                        'id': el['id'],
                        'centro_lat': el['center']['lat'],
                        'centro_lon': el['center']['lon'],
                        'geometria': [],
                        'area_m2': 150
                    })
            if buildings:
                return pd.DataFrame(buildings)
    except Exception as e:
        print(f"Erro OSM: {e}")

    print("⚠️ Usando Mock de Edificações")
    return _mock_buildings(lat, lon)