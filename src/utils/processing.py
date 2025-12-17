import numpy as np


def gerar_grid_varredura(lat_centro, lon_centro, raio_km=0.5, step_metros=100):
    """
    Gera uma lista de coordenadas (lat/long) ao redor de um ponto central
    para fazer a varredura do satélite.

    raio_km: O tamanho da 'fronteira' que vamos assumir.
    step_metros: A cada quantos metros tiramos uma foto? (100m é bom p/ Google Earth)
    """
    # Aproximação simples: 1 grau de lat ~= 111km
    deg_per_km = 1 / 111.0
    change_lat = (step_metros / 1000.0) * deg_per_km
    change_lon = (step_metros / 1000.0) * deg_per_km

    # Cria os pontos
    grid_points = []

    # Varre de -raio até +raio
    lat_start = lat_centro - (raio_km * deg_per_km)
    lat_end = lat_centro + (raio_km * deg_per_km)
    lon_start = lon_centro - (raio_km * deg_per_km)
    lon_end = lon_centro + (raio_km * deg_per_km)

    curr_lat = lat_start
    while curr_lat < lat_end:
        curr_lon = lon_start
        while curr_lon < lon_end:
            grid_points.append({'latitude': curr_lat, 'longitude': curr_lon})
            curr_lon += change_lon
        curr_lat += change_lat

    return grid_points