"""Importação e consulta das notas fiscais esperadas — planilha diária "Entrada
Estoque" exportada do ERP. Usada no Recebimento para conferir automaticamente o que
o conferente digita contra o que a nota realmente contém (produto e quantidade)."""

import pandas as pd
import streamlit as st

from data.db import buscar_todas_linhas, obter_cliente

# Nome da coluna na planilha de origem -> nome do campo aqui. As colunas do ERP às
# vezes vêm com espaços extras no cabeçalho; tratamos isso antes de mapear.
COLUNAS_ORIGEM = {
    "Nota": "numero_nf",
    "Produto": "codigo_produto",
    "Qtde": "quantidade_esperada",
    "Unidade": "unidade",
    "Nome": "fornecedor",
    "Dt. Operacao": "data_operacao",
}


def importar_notas_esperadas(arquivo) -> dict:
    """Lê o .xlsx de Entrada Estoque e grava (upsert) em stockflow_notas_esperadas.
    Linhas repetidas de um mesmo (nota, produto) são somadas."""
    df = pd.read_excel(arquivo, sheet_name=0)
    df.columns = [str(c).strip() for c in df.columns]

    faltando = [c for c in COLUNAS_ORIGEM if c not in df.columns]
    if faltando:
        raise ValueError(f"Colunas esperadas não encontradas no arquivo: {', '.join(faltando)}")

    df = df[list(COLUNAS_ORIGEM)].rename(columns=COLUNAS_ORIGEM)
    df["numero_nf"] = df["numero_nf"].astype(str).str.strip()
    df["codigo_produto"] = pd.to_numeric(df["codigo_produto"], errors="coerce")
    df["quantidade_esperada"] = pd.to_numeric(df["quantidade_esperada"], errors="coerce").fillna(0)
    df["unidade"] = df["unidade"].astype(str).str.strip()
    df["fornecedor"] = df["fornecedor"].astype(str).str.strip()
    df["data_operacao"] = pd.to_datetime(df["data_operacao"], errors="coerce").dt.date.astype(str)
    df = df.dropna(subset=["codigo_produto", "numero_nf"])
    df = df[df["numero_nf"] != ""]

    agrupado = (
        df.groupby(["numero_nf", "codigo_produto"], as_index=False)
        .agg(
            quantidade_esperada=("quantidade_esperada", "sum"),
            unidade=("unidade", "first"),
            fornecedor=("fornecedor", "first"),
            data_operacao=("data_operacao", "first"),
        )
    )
    agrupado["codigo_produto"] = agrupado["codigo_produto"].astype(int)
    agrupado["quantidade_esperada"] = agrupado["quantidade_esperada"].astype(int)

    registros = agrupado.to_dict("records")
    if registros:
        cliente = obter_cliente()
        cliente.table("stockflow_notas_esperadas").upsert(registros, on_conflict="numero_nf,codigo_produto").execute()
        buscar_nota_esperada.clear()

        # Fornecedores novos da nota entram no cadastro dinâmico, para já aparecerem
        # como opção normal no dropdown do Recebimento.
        fornecedores_novos = sorted({f for f in agrupado["fornecedor"] if f})
        if fornecedores_novos:
            from data.cadastros import carregar_lista, salvar_lista
            atuais = set(carregar_lista("fornecedor"))
            if not atuais.issuperset(fornecedores_novos):
                salvar_lista("fornecedor", sorted(atuais | set(fornecedores_novos)))

    return {"notas": int(agrupado["numero_nf"].nunique()), "linhas": len(agrupado)}


@st.cache_data(ttl=600)
def buscar_nota_esperada(numero_nf: str) -> list:
    if not numero_nf or not numero_nf.strip():
        return []
    return buscar_todas_linhas("stockflow_notas_esperadas", filtros={"numero_nf": numero_nf.strip()})
