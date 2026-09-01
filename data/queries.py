"""Toda leitura e escrita das ocorrências de avaria vive aqui. A fonte é o Supabase
(tabela stockflow_ocorrencias) — histórico migrado da planilha original + lançamentos
manuais feitos pelo formulário BOA, todos na mesma tabela na nuvem."""

from datetime import datetime

import pandas as pd
import streamlit as st

from data.db import buscar_todas_linhas, limpar_nulos, obter_cliente

COLUNAS = [
    "id", "fonte", "hora_inicio", "hora_conclusao", "revenda", "conferente",
    "data_ocorrencia", "codigo_produto", "quantidade", "motivo", "placa", "motorista",
    "justificativa", "area", "responsavel", "funcao_colaborador", "turno",
]

CAMPOS_FORMULARIO = [
    "revenda", "conferente", "data_ocorrencia", "codigo_produto", "quantidade",
    "motivo", "placa", "motorista", "justificativa", "area", "responsavel",
    "funcao_colaborador", "turno",
]


def _tratar(df):
    df = df.copy()
    df["data_ocorrencia"] = pd.to_datetime(df["data_ocorrencia"], errors="coerce")
    df["turno"] = df["turno"].astype("string").str.strip().str.upper()
    df["motivo"] = df["motivo"].astype("string").str.strip().str.upper()
    df["area"] = df["area"].astype("string").str.strip()
    df["conferente"] = df["conferente"].astype("string").str.strip().str.upper()
    df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce").fillna(0)
    df["codigo_produto"] = pd.to_numeric(df["codigo_produto"], errors="coerce")
    df = df.dropna(subset=["data_ocorrencia"])
    return df


@st.cache_data(ttl=600)
def carregar_ocorrencias() -> pd.DataFrame:
    linhas = buscar_todas_linhas("stockflow_ocorrencias")
    if not linhas:
        return pd.DataFrame(columns=COLUNAS)
    df = pd.DataFrame(linhas).reindex(columns=COLUNAS)
    return _tratar(df)


def valores_unicos(df, coluna):
    return sorted(df[coluna].dropna().astype(str).str.strip().unique().tolist())


def salvar_registro(dados: dict) -> int:
    """Insere um novo registro em stockflow_ocorrencias e invalida o cache de leitura."""
    cliente = obter_cliente()
    agora = datetime.now().isoformat()

    linha = {c: dados.get(c) for c in CAMPOS_FORMULARIO}
    linha.update({"fonte": "manual", "hora_inicio": agora, "hora_conclusao": agora})
    linha = limpar_nulos(linha)

    resp = cliente.table("stockflow_ocorrencias").insert(linha).execute()
    carregar_ocorrencias.clear()
    return resp.data[0]["id"]
