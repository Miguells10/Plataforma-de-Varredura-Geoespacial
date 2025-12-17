import pandas as pd
import requests
import streamlit as st

import os

RESOURCE_ID = os.getenv("ANEEL_RESOURCE_ID")
BASE_URL = "https://dadosabertos.aneel.gov.br/api/3/action/datastore_search_sql"


@st.cache_data(ttl=3600)
def buscar_usinas_solares(cidade=None, limite=100):
    """
    Busca usinas solares na API da ANEEL usando SQL.
    """
    # 1. Base da query: Filtrar por Solar
    # Nota: Usamos LIKE %%Solar%% porque o % é caractere especial no Python
    query_sql = f"""
        SELECT * from "{RESOURCE_ID}"
        WHERE "DscOrigemCombustivel" LIKE '%%Solar%%'
    """

    # 2. Filtro de Cidade (Corrigido para DscMuninicpios e usando LIKE)
    if cidade:
        # O % extra é para o SQL entender que é uma busca parcial ("BELO HORIZONTE" acha "BELO HORIZONTE - MG")
        cidade_upper = cidade.upper()
        query_sql += f" AND UPPER(\"DscMuninicpios\") LIKE '%%{cidade_upper}%%'"

    query_sql += f" LIMIT {limite}"

    params = {'sql': query_sql}

    try:
        response = requests.get(BASE_URL, params=params)
        data = response.json()

        if data.get('success'):
            df = pd.DataFrame(data['result']['records'])

            # Tratamento de erro caso a busca venha vazia
            if df.empty:
                return df

            # 3. Correção Crítica de Coordenadas (Vírgula para Ponto)
            cols_coords = ['NumCoordNEmpreendimento', 'NumCoordEEmpreendimento']
            for col in cols_coords:
                if col in df.columns:
                    # Remove pontos de milhar se houver e troca vírgula decimal por ponto
                    df[col] = df[col].astype(str).str.replace(',', '.')
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # 4. Renomear para o mapa do Streamlit entender
            df = df.rename(columns={
                'NumCoordNEmpreendimento': 'latitude',
                'NumCoordEEmpreendimento': 'longitude'
            })

            # Converter Potência para número também
            if 'MdaPotenciaOutorgadaKw' in df.columns:
                df['MdaPotenciaOutorgadaKw'] = df['MdaPotenciaOutorgadaKw'].astype(str).str.replace(',', '.').astype(
                    float)

            return df
        else:
            # Mostra o erro na tela para ajudar a debugar
            st.error(f"Erro SQL da API: {data.get('error')}")
            return pd.DataFrame()

    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame()