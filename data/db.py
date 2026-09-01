"""Cliente Supabase compartilhado. Lê a URL e a service role key de st.secrets —
nunca hardcode credenciais aqui. A service role key só é segura porque este código
roda no servidor (Streamlit); nunca é enviada ao navegador do usuário."""

import httpx
import streamlit as st
from supabase import Client, create_client
from supabase.client import ClientOptions


@st.cache_resource
def obter_cliente() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_SERVICE_KEY"]

    # Só usado localmente quando a cadeia de certificados da máquina está incompleta
    # (ex.: proxy corporativo). Em produção (Streamlit Cloud) isso não é necessário —
    # não defina DISABLE_SSL_VERIFY no secrets.toml de produção.
    httpx_client = None
    if st.secrets.get("DISABLE_SSL_VERIFY", False):
        httpx_client = httpx.Client(verify=False)

    return create_client(url, key, options=ClientOptions(httpx_client=httpx_client))


def buscar_todas_linhas(tabela: str, select: str = "*", filtros: dict | None = None) -> list:
    """Busca todas as linhas de uma tabela, paginando de 1000 em 1000 (limite do PostgREST)."""
    cliente = obter_cliente()
    todas, inicio, tamanho = [], 0, 1000
    while True:
        query = cliente.table(tabela).select(select).range(inicio, inicio + tamanho - 1)
        for coluna, valor in (filtros or {}).items():
            query = query.eq(coluna, valor)
        lote = query.execute().data
        todas.extend(lote)
        if len(lote) < tamanho:
            break
        inicio += tamanho
    return todas


def limpar_nulos(dados: dict) -> dict:
    """Converte strings vazias em None antes de gravar (evita erro em colunas numéricas/FK)."""
    return {k: (None if v == "" else v) for k, v in dados.items()}
