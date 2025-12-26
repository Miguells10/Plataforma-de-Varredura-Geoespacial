import math
import random


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calcula distância em km entre dois pontos."""
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def generate_grid_points(center_lat, center_lon, radius_km=0.5, spacing_meters=30):
    """Gera grid matemático simples (sem H3)."""
    points = []
    try:
        # 1 grau lat ~ 111km
        lat_step = (spacing_meters / 1000.0) / 111.0
        lon_step = (spacing_meters / 1000.0) / (111.0 * math.cos(math.radians(center_lat)))

        num_steps = int(radius_km / (spacing_meters / 1000.0))

        for i in range(-num_steps, num_steps + 1):
            for j in range(-num_steps, num_steps + 1):
                lat = center_lat + i * lat_step
                lon = center_lon + j * lon_step

                if haversine_distance(center_lat, center_lon, lat, lon) <= radius_km:
                    points.append({
                        'id': f'grid_{i}_{j}',
                        'latitude': lat,
                        'longitude': lon,
                        'categoria_osm': 'Grid Matemático',
                        'type': 'grid',
                        'geometria': []
                    })
        return points
    except Exception as e:
        print(f"Erro grid: {e}")
        return []


def prepare_scan_data(center_lat, center_lon, buildings=[], radius_km=0.5, modo="osm"):
    """
    Prepara a lista final de pontos para o scan.
    Lógica: Tenta usar Buildings. Se não der (ou modo for grid), usa Grid.
    """
    final_points = []

    use_buildings = (modo == "osm")

    if use_buildings and buildings:
        print(f"🏠 Usando {len(buildings)} edificações do OSM...")
        for b in buildings:
            lat = b.get('center', {}).get('lat') or b.get('centro_lat') or b.get('latitude')
            lon = b.get('center', {}).get('lon') or b.get('centro_lon') or b.get('longitude')
            geo = b.get('geometry') or b.get('geometria', [])
            cat = b.get('categoria_osm', 'Desconhecido')
            uid = b.get('id', 'N/A')

            if lat and lon:
                final_points.append({
                    'id': uid,
                    'latitude': lat,
                    'longitude': lon,
                    'categoria_osm': cat,
                    'type': 'building',
                    'geometria': geo
                })

    if not final_points:
        print("📐 Gerando Grid Matemático (Modo Rural/Grid)...")
        final_points = generate_grid_points(center_lat, center_lon, radius_km)

    if not final_points:
        print("⚠️ Fallback Emergência (Pontos Aleatórios)...")
        for k in range(15):
            lat_rand = center_lat + random.uniform(-0.003, 0.003)
            lon_rand = center_lon + random.uniform(-0.003, 0.003)
            final_points.append({
                'id': f'fallback_{k}',
                'latitude': lat_rand,
                'longitude': lon_rand,
                'categoria_osm': 'Simulação',
                'type': 'random',
                'geometria': []
            })

    return final_points