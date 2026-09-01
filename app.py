"""Roteador de UI. Sem query nem cálculo aqui — só composição de layout."""

from pathlib import Path

import streamlit as st

from config import CORES, META_AVARIA_PRODUTO_PCT, META_TURNO_CONCENTRACAO
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

st.set_page_config(page_title="StockFlow — Ocorrências de Avaria", page_icon="📦", layout="wide")
st.markdown(f"<style>{Path('assets/styles.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

df_completo = carregar_ocorrencias()

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="logo-box">📦</div>
            <div>
                <div class="brand-title">StockFlow</div>
                <div class="brand-sub">Gestão de Armazéns</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    pagina = st.radio(
        "Navegação",
        [
            "📊  Dashboard", "📥  Recebimento", "⚠️  BOA", "📦  Estoque", "🧭  Picking",
            "🚚  Expedição", "🗂️  Inventário", "📋  Cadastro", "📈  Relatórios", "🎯  Indicadores",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("**Filtros**")

    data_min = df_completo["data_ocorrencia"].min().date()
    data_max = df_completo["data_ocorrencia"].max().date()
    intervalo = st.date_input("Período", value=(data_min, data_max), min_value=data_min, max_value=data_max)
    data_inicio, data_fim = intervalo if len(intervalo) == 2 else (data_min, data_max)

    turnos_sel = st.multiselect("Turno", sorted(df_completo["turno"].dropna().unique()))
    areas_sel = st.multiselect("Área", sorted(df_completo["area"].dropna().unique()))
    motivos_sel = st.multiselect("Motivo", sorted(df_completo["motivo"].dropna().unique()))
    conferentes_sel = st.multiselect("Conferente", sorted(df_completo["conferente"].dropna().unique()))

    st.markdown(
        """
        <div class="sidebar-footer">
            <b>StockFlow WMS</b><br>
            Painel de ocorrências de avaria construído a partir do Boletim de Ocorrência real do armazém.
        </div>
        """,
        unsafe_allow_html=True,
    )

if pagina == "📥  Recebimento":
    st.markdown("<div class='page-header'><h1>Recebimento</h1></div>", unsafe_allow_html=True)
    from ui.recebimento import pagina_recebimento
    pagina_recebimento()
    st.stop()

if pagina == "⚠️  BOA":
    st.markdown("<div class='page-header'><h1>BOA — Registro de Ocorrência</h1></div>", unsafe_allow_html=True)
    from ui.forms import formulario_registro
    formulario_registro()
    st.stop()

if pagina == "📋  Cadastro":
    st.markdown("<div class='page-header'><h1>Cadastro</h1></div>", unsafe_allow_html=True)
    from ui.cadastro import pagina_cadastro
    pagina_cadastro()
    st.stop()

if pagina != "📊  Dashboard":
    st.markdown(f"<div class='page-header'><h1>{pagina.split(' ', 1)[1].strip()}</h1></div>", unsafe_allow_html=True)
    st.info("Módulo em construção — este protótipo cobre apenas o Dashboard de Ocorrências de Avaria, com dados reais.")
    st.stop()

df = filtrar(df_completo, data_inicio, data_fim, turnos_sel, areas_sel, motivos_sel, conferentes_sel)

st.markdown(
    f"""
    <div class="page-header">
        <div>
            <h1>DASHBOARD DE OCORRÊNCIAS DE AVARIA</h1>
            <div class="subtitle">Boletim de Ocorrência — Revenda Pinheiro · {len(df)} registros no período selecionado</div>
        </div>
        <div class="badge-sync">✓ Sincronizado com o Supabase</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if df.empty:
    st.warning("Nenhuma ocorrência encontrada para os filtros selecionados.")
    st.stop()

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
        st.plotly_chart(
            grafico_tendencia_mensal(serie_mensal(df), kpis["ocorrencias"]["meta"]),
            width='stretch',
        )
with col_b:
    with st.container(border=True):
        st.plotly_chart(grafico_composicao_area(por_area(df)), width='stretch')

col_c, col_d = st.columns(2)
with col_c:
    with st.container(border=True):
        st.plotly_chart(
            grafico_barra_horizontal(por_motivo(df), "motivo", "ocorrencias", "Top motivos de avaria", CORES["primaria"]),
            width='stretch',
        )
with col_d:
    with st.container(border=True):
        st.plotly_chart(grafico_turno(por_turno(df), META_TURNO_CONCENTRACAO), width='stretch')

with st.container(border=True):
    st.plotly_chart(
        grafico_barra_horizontal(por_conferente(df), "conferente", "ocorrencias", "Ranking de conferentes", CORES["secundaria"]),
        width='stretch',
    )

st.markdown("<div class='section-title'>Detalhamento das ocorrências</div>", unsafe_allow_html=True)
with st.container(border=True):
    render_tabela(tabela_drilldown(df))
