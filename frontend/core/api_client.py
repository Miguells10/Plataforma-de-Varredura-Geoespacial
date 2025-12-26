import requests
import pandas as pd
import streamlit as st
from frontend.core.settings import API_BASE_URL


class RadixAPI:
    """Cliente HTTP para comunicação com o Backend FastAPI."""

    @staticmethod
    def check_health():
        try:
            resp = requests.get(f"{API_BASE_URL}/", timeout=2)
            return resp.status_code == 200
        except:
            return False

    @staticmethod
    def get_subestacoes(cidade: str):
        try:
            resp = requests.get(f"{API_BASE_URL}/subestacoes", params={"cidade": cidade})
            if resp.status_code == 200:
                return pd.DataFrame(resp.json())
        except Exception as e:
            st.error(f"Erro de comunicação: {e}")
        return pd.DataFrame()

    @staticmethod
    def executar_scan(payload: dict):
        """Envia requisição de processamento pesado."""
        try:
            resp = requests.post(f"{API_BASE_URL}/scan", json=payload, timeout=60)
            if resp.status_code == 200:
                return resp.json()
            else:
                st.error(f"Erro na API ({resp.status_code}): {resp.text}")
                return None
        except Exception as e:
            st.error(f"Falha na conexão: {e}")
            return None