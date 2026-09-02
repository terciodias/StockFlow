"""Roteador de UI, estilo app de celular: tela inicial de cartões (funções) e cada
seção abre em tela cheia com um botão de voltar. Sem menu lateral."""

from pathlib import Path

import streamlit as st

st.set_page_config(page_title="StockFlow", page_icon="📦", layout="wide")
st.markdown(f"<style>{Path('assets/styles.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

if "view" not in st.session_state:
    st.session_state.view = "home"


def ir(view):
    st.session_state.view = view
    st.rerun()


def cabecalho():
    st.markdown(
        """
        <div class="app-header">
            <div class="app-brand">
                <div class="app-logo">📦</div>
                <div>
                    <div class="app-title">StockFlow</div>
                    <div class="app-sub">Gestão de Armazém</div>
                </div>
            </div>
            <div class="app-status">● Sincronizado</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Cada cartão: chave interna, emoji, título, descrição e classe de cor.
CARTOES = [
    ("recebimento", "📥", "Recebimento", "Registrar chegada de carga e conferir notas fiscais.", "azul"),
    ("boa", "⚠️", "BOA — Avaria", "Lançar ocorrências de avaria e falta de produto.", "vermelho"),
    ("dashboard", "📊", "Dashboard", "Ver indicadores e gráficos das ocorrências.", "verde"),
    ("cadastro", "📋", "Cadastro", "Manter produtos e as listas usadas nos formulários.", "roxo"),
]


def tela_inicial():
    cabecalho()
    st.markdown(
        """
        <div class="home-hero">
            <div class="home-hero-title">Como você vai usar agora?</div>
            <div class="home-hero-sub">Escolha sua função. Dá para trocar depois.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, col_meio, _ = st.columns([1, 3, 1])
    with col_meio:
        with st.container(key="home_cards"):
            for chave, emoji, titulo, descricao, cor in CARTOES:
                if st.button(f"{emoji}  **{titulo}**  \n{descricao}", key=f"card_{chave}", use_container_width=True):
                    ir(chave)


def barra_voltar(titulo):
    col_btn, col_titulo = st.columns([1, 5])
    with col_btn:
        if st.button("← Voltar", key="voltar", use_container_width=True):
            ir("home")
    with col_titulo:
        st.markdown(f"<div class='sec-title'>{titulo}</div>", unsafe_allow_html=True)


view = st.session_state.view

if view == "home":
    tela_inicial()
    st.stop()

cabecalho()

if view == "recebimento":
    barra_voltar("Recebimento")
    from ui.recebimento import pagina_recebimento
    pagina_recebimento()

elif view == "boa":
    barra_voltar("BOA — Registro de Ocorrência")
    from ui.forms import formulario_registro
    formulario_registro()

elif view == "cadastro":
    barra_voltar("Cadastro")
    from ui.cadastro import pagina_cadastro
    pagina_cadastro()

elif view == "dashboard":
    barra_voltar("Dashboard de Ocorrências de Avaria")
    from ui.dashboard import pagina_dashboard
    pagina_dashboard()
