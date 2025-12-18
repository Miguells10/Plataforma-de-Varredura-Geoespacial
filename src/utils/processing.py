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
                        'latitude': lat,
                        'longitude': lon,
                        'type': 'grid',
                        'geometria': []
                    })
        return points
    except Exception as e:
        print(f"Erro grid: {e}")
        return []


def prepare_scan_data(center_lat, center_lon, buildings=[], radius_km=0.5, use_buildings=True):
    """Prepara a lista final de pontos para o scan."""
    final_points = []

    if use_buildings and buildings:
        print(f"Usando {len(buildings)} edificações...")
        for b in buildings:
            # Tenta pegar o centro de várias formas
            lat = b.get('center', {}).get('lat') or b.get('centro_lat')
            lon = b.get('center', {}).get('lon') or b.get('centro_lon')
            geo = b.get('geometry') or b.get('geometria')

            if lat and lon:
                final_points.append({
                    'latitude': lat,
                    'longitude': lon,
                    'type': 'building',
                    'geometria': geo
                })

    if not final_points:
        print("Gerando Grid Matemático...")
        final_points = generate_grid_points(center_lat, center_lon, radius_km)

    # 3. Fallback de Emergência (Se tudo falhar, gera aleatório)
    if not final_points:
        print("Fallback Emergência...")
        for _ in range(20):
            final_points.append({
                'latitude': center_lat + random.uniform(-0.005, 0.005),
                'longitude': center_lon + random.uniform(-0.005, 0.005),
                'type': 'random',
                'geometria': []
            })

    return final_points