"""Leitura e escrita dos cadastros dinâmicos (produtos e demais listas usadas nos
dropdowns do BOA e do Recebimento) na tabela stockflow_produtos / stockflow_listas
do Supabase."""

import pandas as pd
import streamlit as st

from data.db import buscar_todas_linhas, obter_cliente


@st.cache_data(ttl=600)
def carregar_produtos() -> pd.DataFrame:
    linhas = buscar_todas_linhas("stockflow_produtos")
    if not linhas:
        return pd.DataFrame(columns=["codigo_produto", "nome_produto"])
    df = pd.DataFrame(linhas)
    df["codigo_produto"] = pd.to_numeric(df["codigo_produto"], errors="coerce")
    df["nome_produto"] = df["nome_produto"].fillna("").astype(str)
    return (
        df[["codigo_produto", "nome_produto"]]
        .dropna(subset=["codigo_produto"])
        .sort_values("codigo_produto")
        .reset_index(drop=True)
    )


def salvar_produtos(df: pd.DataFrame) -> None:
    cliente = obter_cliente()
    limpo = df.dropna(subset=["codigo_produto"]).copy()
    limpo["codigo_produto"] = limpo["codigo_produto"].astype(int)
    limpo["nome_produto"] = limpo["nome_produto"].fillna("").astype(str).str.strip()
    limpo = limpo.drop_duplicates("codigo_produto")

    codigos_atuais = set(carregar_produtos()["codigo_produto"])
    codigos_novos = set(limpo["codigo_produto"])
    removidos = codigos_atuais - codigos_novos
    if removidos:
        cliente.table("stockflow_produtos").delete().in_("codigo_produto", list(removidos)).execute()

    registros = limpo[["codigo_produto", "nome_produto"]].to_dict("records")
    if registros:
        cliente.table("stockflow_produtos").upsert(registros, on_conflict="codigo_produto").execute()

    carregar_produtos.clear()


def buscar_nome_produto(codigo) -> str:
    if codigo is None or pd.isna(codigo):
        return ""
    df = carregar_produtos()
    linha = df[df["codigo_produto"] == int(codigo)]
    if linha.empty:
        return ""
    return linha.iloc[0]["nome_produto"]


@st.cache_data(ttl=600)
def carregar_lista(campo: str) -> list:
    linhas = buscar_todas_linhas("stockflow_listas", filtros={"campo": campo})
    return sorted({str(l["valor"]).strip() for l in linhas if l.get("valor")})


def salvar_lista(campo: str, valores: list) -> None:
    cliente = obter_cliente()
    limpos = sorted({str(v).strip() for v in valores if str(v).strip()})
    cliente.table("stockflow_listas").delete().eq("campo", campo).execute()
    if limpos:
        registros = [{"campo": campo, "valor": v} for v in limpos]
        cliente.table("stockflow_listas").insert(registros).execute()
    carregar_lista.clear()
