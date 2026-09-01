"""ETL local e cálculo de indicadores. Funções puras: recebem DataFrame, devolvem
DataFrame/valor. Nada de `st.*` aqui — isso mantém a lógica testável fora do Streamlit."""

import pandas as pd

from config import (
    LIMIAR_QTD_ATENCAO,
    LIMIAR_QTD_CRITICO,
    META_AVARIA_PRODUTO_PCT,
    META_TURNO_CONCENTRACAO,
    MOTIVOS_AVARIA_PRODUTO,
    TOLERANCIA_AMARELO,
)


def filtrar(df, data_inicio, data_fim, turnos=None, areas=None, motivos=None, conferentes=None):
    out = df[(df["data_ocorrencia"] >= pd.Timestamp(data_inicio)) & (df["data_ocorrencia"] <= pd.Timestamp(data_fim))]
    if turnos:
        out = out[out["turno"].isin(turnos)]
    if areas:
        out = out[out["area"].isin(areas)]
    if motivos:
        out = out[out["motivo"].isin(motivos)]
    if conferentes:
        out = out[out["conferente"].isin(conferentes)]
    return out


def status_regra(real, meta, tolerancia=TOLERANCIA_AMARELO, maior_melhor=False):
    """Compara real x meta considerando a direção esperada e devolve verde/amarelo/vermelho."""
    if meta == 0:
        return "verde"
    desvio = (real - meta) / meta
    if not maior_melhor:
        desvio = -desvio
    if desvio >= 0:
        return "verde"
    if desvio >= -tolerancia:
        return "amarelo"
    return "vermelho"


def serie_mensal(df):
    s = (
        df.assign(mes=df["data_ocorrencia"].dt.to_period("M").dt.to_timestamp())
        .groupby("mes")
        .agg(ocorrencias=("id", "count"), quantidade=("quantidade", "sum"))
        .reset_index()
        .sort_values("mes")
    )
    return s


def media_mensal_historica(df_completo):
    """Baseline de referência calculado sobre a base inteira (não filtrada), usado como meta."""
    s = serie_mensal(df_completo)
    if s.empty:
        return {"ocorrencias": 0.0, "quantidade": 0.0}
    return {"ocorrencias": s["ocorrencias"].mean(), "quantidade": s["quantidade"].mean()}


def por_motivo(df, top_n=10):
    g = (
        df.groupby("motivo")
        .agg(ocorrencias=("id", "count"), quantidade=("quantidade", "sum"))
        .reset_index()
        .sort_values("ocorrencias", ascending=False)
    )
    return g.head(top_n)


def por_area(df):
    g = (
        df.groupby("area")
        .agg(ocorrencias=("id", "count"), quantidade=("quantidade", "sum"))
        .reset_index()
        .sort_values("ocorrencias", ascending=False)
    )
    return g


def por_turno(df):
    g = (
        df.groupby("turno")
        .agg(ocorrencias=("id", "count"), quantidade=("quantidade", "sum"))
        .reset_index()
        .sort_values("turno")
    )
    total = g["ocorrencias"].sum()
    g["pct"] = g["ocorrencias"] / total if total else 0
    return g


def por_conferente(df, top_n=10):
    g = (
        df.groupby("conferente")
        .agg(ocorrencias=("id", "count"), quantidade=("quantidade", "sum"))
        .reset_index()
        .sort_values("ocorrencias", ascending=False)
    )
    return g.head(top_n)


def calcular_kpis(df, df_completo):
    total_ocorrencias = len(df)
    total_quantidade = df["quantidade"].sum()
    baseline = media_mensal_historica(df_completo)

    turno_g = por_turno(df)
    turno_top = turno_g.sort_values("pct", ascending=False).iloc[0] if not turno_g.empty else None
    pct_turno_top = float(turno_top["pct"]) if turno_top is not None else 0.0
    turno_nome = turno_top["turno"] if turno_top is not None else "-"

    pct_avaria_produto = (
        df[df["motivo"].isin(MOTIVOS_AVARIA_PRODUTO)].shape[0] / total_ocorrencias
        if total_ocorrencias else 0.0
    )

    return {
        "ocorrencias": {
            "real": total_ocorrencias,
            "meta": baseline["ocorrencias"],
            "status": status_regra(total_ocorrencias, baseline["ocorrencias"], maior_melhor=False),
        },
        "quantidade": {
            "real": total_quantidade,
            "meta": baseline["quantidade"],
            "status": status_regra(total_quantidade, baseline["quantidade"], maior_melhor=False),
        },
        "turno_concentracao": {
            "real": pct_turno_top,
            "meta": META_TURNO_CONCENTRACAO,
            "turno": turno_nome,
            "status": status_regra(pct_turno_top, META_TURNO_CONCENTRACAO, maior_melhor=False),
        },
        "avaria_produto": {
            "real": pct_avaria_produto,
            "meta": META_AVARIA_PRODUTO_PCT,
            "status": status_regra(pct_avaria_produto, META_AVARIA_PRODUTO_PCT, maior_melhor=False),
        },
    }


def tabela_drilldown(df):
    def status_linha(qtd):
        if qtd >= LIMIAR_QTD_CRITICO:
            return "vermelho"
        if qtd >= LIMIAR_QTD_ATENCAO:
            return "amarelo"
        return "verde"

    out = df.copy()
    out["status"] = out["quantidade"].apply(status_linha)
    cols = [
        "data_ocorrencia", "turno", "area", "motivo", "quantidade",
        "conferente", "motorista", "placa", "justificativa", "status",
    ]
    out = out[cols].sort_values("data_ocorrencia", ascending=False)
    out = out.rename(columns={
        "data_ocorrencia": "Data", "turno": "Turno", "area": "Área",
        "motivo": "Motivo", "quantidade": "Quantidade", "conferente": "Conferente",
        "motorista": "Motorista", "placa": "Placa", "justificativa": "Justificativa",
        "status": "status",
    })
    return out
