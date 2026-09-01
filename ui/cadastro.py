"""Página de Cadastro: mantém dinamicamente os produtos (código + nome/referência)
e as demais listas usadas nos dropdowns do formulário BOA."""

import pandas as pd
import streamlit as st

from config import NOMES_LISTAS_CADASTRAVEIS
from data.cadastros import carregar_lista, carregar_produtos, salvar_lista, salvar_produtos


def pagina_cadastro():
    aba_produtos, aba_listas = st.tabs(["📦 Produtos", "🗂️ Outras Listas"])
    with aba_produtos:
        _render_produtos()
    with aba_listas:
        _render_listas()


def _render_produtos():
    st.markdown("<div class='section-title'>Consulta rápida</div>", unsafe_allow_html=True)
    st.caption("Digite um código ou um nome para ver a referência correspondente.")
    busca = st.text_input("Buscar produto", key="busca_produtos", placeholder="Ex.: 982 ou Cerveja Lata",
                           label_visibility="collapsed")

    df = carregar_produtos()
    if busca.strip():
        termo = busca.strip().lower()
        resultado = df[
            df["codigo_produto"].astype(str).str.contains(termo, na=False)
            | df["nome_produto"].str.lower().str.contains(termo, na=False)
        ]
        with st.container(border=True):
            if resultado.empty:
                st.warning("Nenhum produto encontrado para essa busca.")
            else:
                st.dataframe(
                    resultado.rename(columns={"codigo_produto": "Código", "nome_produto": "Nome / Referência"}),
                    hide_index=True, width="stretch",
                )

    st.markdown("<div class='section-title' style='margin-top:20px;'>Editar cadastro de produtos</div>", unsafe_allow_html=True)
    st.caption("Adicione, renomeie ou remova produtos. Use ➕ para nova linha e a lixeira para excluir.")

    with st.container(border=True):
        editado = st.data_editor(
            df,
            key="editor_produtos",
            num_rows="dynamic",
            width="stretch",
            hide_index=True,
            column_config={
                "codigo_produto": st.column_config.NumberColumn("Código do Produto", min_value=0, step=1, format="%d"),
                "nome_produto": st.column_config.TextColumn("Nome / Referência do Produto"),
            },
        )

    if st.button("Salvar Cadastro de Produtos", type="primary", key="salvar_produtos_btn"):
        salvar_produtos(editado)
        st.success(f"Cadastro de produtos salvo — {len(editado.dropna(subset=['codigo_produto']))} produto(s).")
        st.rerun()


def _render_listas():
    campo = st.selectbox("Selecione a lista", list(NOMES_LISTAS_CADASTRAVEIS.keys()),
                          format_func=lambda c: NOMES_LISTAS_CADASTRAVEIS[c], key="lista_selecionada")

    valores = carregar_lista(campo)

    st.markdown("<div class='section-title'>Consulta rápida</div>", unsafe_allow_html=True)
    busca = st.text_input("Buscar valor", key=f"busca_{campo}", placeholder="Digite para filtrar",
                           label_visibility="collapsed")
    valores_exibidos = [v for v in valores if busca.strip().lower() in v.lower()] if busca.strip() else valores
    with st.container(border=True):
        if not valores_exibidos:
            st.warning("Nenhum valor encontrado para essa busca.")
        else:
            st.dataframe(pd.DataFrame({NOMES_LISTAS_CADASTRAVEIS[campo]: valores_exibidos}), hide_index=True, width="stretch")

    st.markdown(f"<div class='section-title' style='margin-top:20px;'>Editar lista — {NOMES_LISTAS_CADASTRAVEIS[campo]}</div>", unsafe_allow_html=True)
    st.caption("Adicione ou remova valores. Use ➕ para nova linha e a lixeira para excluir.")

    with st.container(border=True):
        editado = st.data_editor(
            pd.DataFrame({"valor": valores}),
            key=f"editor_lista_{campo}",
            num_rows="dynamic",
            width="stretch",
            hide_index=True,
            column_config={"valor": st.column_config.TextColumn(NOMES_LISTAS_CADASTRAVEIS[campo])},
        )

    if st.button(f"Salvar Lista de {NOMES_LISTAS_CADASTRAVEIS[campo]}", type="primary", key=f"salvar_lista_{campo}"):
        salvar_lista(campo, editado["valor"].tolist())
        st.success(f"Lista de {NOMES_LISTAS_CADASTRAVEIS[campo]} salva.")
        st.rerun()
