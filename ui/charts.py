"""Funções que retornam figuras Plotly prontas para st.plotly_chart. Sem st.*_chart,
sem matplotlib/seaborn — só plotly.graph_objects, com paleta e template centralizados."""

import plotly.graph_objects as go

from config import CORES

_LAYOUT_BASE = dict(
    template="plotly_white",
    margin=dict(l=10, r=10, t=40, b=10),
    height=320,
    legend=dict(orientation="h", y=-0.2),
    hovermode="x unified",
)


def grafico_tendencia_mensal(df_serie, meta_ocorrencias, titulo="Ocorrências por mês"):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_serie["mes"], y=df_serie["ocorrencias"],
        mode="lines+markers",
        line=dict(color=CORES["primaria"], width=3),
        marker=dict(size=7),
        hovertemplate="%{x|%b/%Y}<br><b>%{y:.0f} ocorrências</b><extra></extra>",
        name="Ocorrências",
    ))
    if meta_ocorrencias:
        fig.add_hline(
            y=meta_ocorrencias, line_dash="dash", line_color=CORES["meta"],
            annotation_text=f"Média histórica {meta_ocorrencias:.0f}", annotation_position="top left",
        )
    fig.update_layout(title=dict(text=titulo, x=0, font=dict(size=16)), **_LAYOUT_BASE)
    fig.update_yaxes(rangemode="tozero")
    return fig


def grafico_barra_horizontal(df, col_categoria, col_valor, titulo, cor=None, unidade=""):
    df = df.sort_values(col_valor, ascending=True)
    fig = go.Figure(go.Bar(
        x=df[col_valor], y=df[col_categoria], orientation="h",
        marker_color=cor or CORES["primaria"],
        hovertemplate=f"%{{y}}<br><b>%{{x:.0f}}{unidade}</b><extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=titulo, x=0, font=dict(size=16)),
        template="plotly_white",
        margin=dict(l=10, r=10, t=40, b=10),
        height=max(280, 32 * len(df)),
        showlegend=False,
    )
    return fig


def grafico_turno(df_turno, meta_pct, titulo="Concentração de ocorrências por turno"):
    cores = [CORES["critico"] if p > meta_pct else CORES["primaria"] for p in df_turno["pct"]]
    fig = go.Figure(go.Bar(
        x=df_turno["turno"], y=df_turno["pct"],
        marker_color=cores,
        hovertemplate="%{x}<br><b>%{y:.1%}</b> das ocorrências<extra></extra>",
    ))
    fig.add_hline(
        y=meta_pct, line_dash="dash", line_color=CORES["meta"],
        annotation_text=f"Meta de equilíbrio {meta_pct:.0%}", annotation_position="top left",
    )
    fig.update_layout(
        title=dict(text=titulo, x=0, font=dict(size=16)),
        template="plotly_white",
        margin=dict(l=10, r=10, t=40, b=10),
        height=320,
        yaxis=dict(tickformat=".0%"),
        showlegend=False,
    )
    return fig


def grafico_composicao_area(df_area, titulo="Ocorrências por área"):
    total = df_area["ocorrencias"].sum()
    fig = go.Figure(go.Pie(
        labels=df_area["area"], values=df_area["ocorrencias"], hole=0.6,
        marker=dict(colors=CORES["paleta_categorica"], line=dict(color="#FFFFFF", width=2)),
        hovertemplate="%{label}<br><b>%{value} (%{percent})</b><extra></extra>",
        textinfo="none",
        sort=False,
    ))
    fig.add_annotation(
        text=f"<b>{total:.0f}</b><br><span style='font-size:11px;color:#8A8A8A'>ocorrências</span>",
        showarrow=False, font=dict(size=20, color=CORES["texto"]),
    )
    fig.update_layout(
        title=dict(text=titulo, x=0, font=dict(size=16)),
        margin=dict(l=10, r=10, t=40, b=10),
        height=320,
        legend=dict(orientation="v", y=0.5, font=dict(size=11)),
    )
    return fig
