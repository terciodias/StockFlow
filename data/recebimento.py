"""Leitura e escrita das conferências de recebimento na tabela stockflow_recebimentos
do Supabase. Segue o mesmo padrão do BOA: uma "carga" (nota fiscal) pode ter vários
produtos — cada produto vira uma linha, compartilhando os dados de cabeçalho (NF,
fornecedor, transportadora etc.) por meio de um id_recebimento comum."""

from datetime import datetime

import pandas as pd
import streamlit as st

from data.db import buscar_todas_linhas, limpar_nulos, obter_cliente

COLUNAS = [
    "id", "id_recebimento", "data_hora_registro", "data_hora_chegada", "revenda",
    "numero_nf", "fornecedor", "transportadora", "placa", "motorista", "conferente",
    "turno", "status_conferencia", "observacoes_gerais", "codigo_produto",
    "quantidade_pedida", "quantidade_recebida", "diferenca", "quantidade_avariada",
    "motivo_avaria", "observacao_item", "id_ocorrencia_boa",
]


@st.cache_data(ttl=600)
def carregar_recebimentos() -> pd.DataFrame:
    linhas = buscar_todas_linhas("stockflow_recebimentos")
    if not linhas:
        return pd.DataFrame(columns=COLUNAS)
    df = pd.DataFrame(linhas).reindex(columns=COLUNAS)
    df["data_hora_chegada"] = pd.to_datetime(df["data_hora_chegada"], errors="coerce")
    for col in ["quantidade_pedida", "quantidade_recebida", "diferenca", "quantidade_avariada"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df.dropna(subset=["data_hora_chegada"])


def proximo_id_recebimento() -> int:
    cliente = obter_cliente()
    resp = cliente.rpc("stockflow_next_recebimento_id", {}).execute()
    return int(resp.data)


def salvar_item_recebimento(dados: dict) -> int:
    """Insere uma linha (um produto) em stockflow_recebimentos. Retorna o id gerado."""
    cliente = obter_cliente()
    linha = {c: dados.get(c) for c in COLUNAS if c not in ("id", "data_hora_registro")}
    linha["data_hora_registro"] = datetime.now().isoformat()
    linha = limpar_nulos(linha)

    resp = cliente.table("stockflow_recebimentos").insert(linha).execute()
    carregar_recebimentos.clear()
    return resp.data[0]["id"]
