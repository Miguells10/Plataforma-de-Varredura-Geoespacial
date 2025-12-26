import pandas as pd
from scipy.spatial import cKDTree


def filtrar_por_voronoi(lista_casas_dict, df_subestacoes, nome_alvo):
    """
    Filtra as casas mantendo apenas as que pertencem matematicamente à subestação alvo.
    """
    if not lista_casas_dict or df_subestacoes.empty:
        return lista_casas_dict

    df_casas = pd.DataFrame(lista_casas_dict)

    # Validação básica
    if 'latitude' not in df_casas.columns:
        # Tenta recuperar se vier com outros nomes
        if 'centro_lat' in df_casas.columns:
            df_casas['latitude'] = df_casas['centro_lat']
            df_casas['longitude'] = df_casas['centro_lon']
        else:
            return lista_casas_dict

    # Prepara Voronoi (KDTree)
    coords_subs = df_subestacoes[['latitude', 'longitude']].values
    nomes_subs = df_subestacoes['Nome'].values

    arvore = cKDTree(coords_subs)

    # Consulta
    coords_casas = df_casas[['latitude', 'longitude']].values
    _, indices = arvore.query(coords_casas, k=1)

    # Atribui dono
    df_casas['dono'] = nomes_subs[indices]

    # Filtra
    df_final = df_casas[df_casas['dono'] == nome_alvo]

    return df_final.to_dict('records')