"""Página de Dashboard de ocorrências de avaria. Os filtros, antes na barra lateral,
agora ficam num expansor no topo da própria página."""

import streamlit as st

from config import CORES, META_TURNO_CONCENTRACAO
from data.queries import carregar_ocorrencias
from data.transforms import (
    calcular_kpis,
    filtrar,
    por_area,
    por_conferente,
    por_motivo,
    por_turno,
    serie_mensal,
    tabela_drilldown,
)
from ui.cards import card_kpi
from ui.charts import (
    grafico_barra_horizontal,
    grafico_composicao_area,
    grafico_tendencia_mensal,
    grafico_turno,
)
from ui.tables import tabela_drilldown as render_tabela


def pagina_dashboard():
    df_completo = carregar_ocorrencias()
    if df_completo.empty:
        st.warning("Nenhuma ocorrência registrada ainda.")
        return

    data_min = df_completo["data_ocorrencia"].min().date()
    data_max = df_completo["data_ocorrencia"].max().date()

    with st.expander("🔎 Filtros", expanded=False):
        intervalo = st.date_input("Período", value=(data_min, data_max), min_value=data_min, max_value=data_max)
        data_inicio, data_fim = intervalo if len(intervalo) == 2 else (data_min, data_max)
        col1, col2 = st.columns(2)
        with col1:
            turnos_sel = st.multiselect("Turno", sorted(df_completo["turno"].dropna().unique()))
            areas_sel = st.multiselect("Área", sorted(df_completo["area"].dropna().unique()))
        with col2:
            motivos_sel = st.multiselect("Motivo", sorted(df_completo["motivo"].dropna().unique()))
            conferentes_sel = st.multiselect("Conferente", sorted(df_completo["conferente"].dropna().unique()))

    df = filtrar(df_completo, data_inicio, data_fim, turnos_sel, areas_sel, motivos_sel, conferentes_sel)

    st.markdown(
        f"<div class='subtitle' style='margin-bottom:12px;'>{len(df)} registros no período selecionado</div>",
        unsafe_allow_html=True,
    )

    if df.empty:
        st.warning("Nenhuma ocorrência encontrada para os filtros selecionados.")
        return

    kpis = calcular_kpis(df, df_completo)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card_kpi("Ocorrências no período", kpis["ocorrencias"]["real"], kpis["ocorrencias"]["meta"],
                 kpis["ocorrencias"]["status"], fmt="{:.0f}")
    with c2:
        card_kpi("Unidades avariadas", kpis["quantidade"]["real"], kpis["quantidade"]["meta"],
                 kpis["quantidade"]["status"], fmt="{:.0f}")
    with c3:
        card_kpi(f"Concentração — {kpis['turno_concentracao']['turno']}", kpis["turno_concentracao"]["real"] * 100,
                 kpis["turno_concentracao"]["meta"] * 100, kpis["turno_concentracao"]["status"],
                 fmt="{:.1f}", sufixo="%", subtitulo_meta="Meta de equilíbrio")
    with c4:
        card_kpi("Avaria de produto (evitável)", kpis["avaria_produto"]["real"] * 100,
                 kpis["avaria_produto"]["meta"] * 100, kpis["avaria_produto"]["status"],
                 fmt="{:.1f}", sufixo="%", subtitulo_meta="Meta máxima")

    st.write("")

    col_a, col_b = st.columns([2, 1])
    with col_a:
        with st.container(border=True):
            st.plotly_chart(grafico_tendencia_mensal(serie_mensal(df), kpis["ocorrencias"]["meta"]), width="stretch")
    with col_b:
        with st.container(border=True):
            st.plotly_chart(grafico_composicao_area(por_area(df)), width="stretch")

    col_c, col_d = st.columns(2)
    with col_c:
        with st.container(border=True):
            st.plotly_chart(
                grafico_barra_horizontal(por_motivo(df), "motivo", "ocorrencias", "Top motivos de avaria", CORES["primaria"]),
                width="stretch",
            )
    with col_d:
        with st.container(border=True):
            st.plotly_chart(grafico_turno(por_turno(df), META_TURNO_CONCENTRACAO), width="stretch")

    with st.container(border=True):
        st.plotly_chart(
            grafico_barra_horizontal(por_conferente(df), "conferente", "ocorrencias", "Ranking de conferentes", CORES["secundaria"]),
            width="stretch",
        )

    st.markdown("<div class='section-title'>Detalhamento das ocorrências</div>", unsafe_allow_html=True)
    with st.container(border=True):
        render_tabela(tabela_drilldown(df))
