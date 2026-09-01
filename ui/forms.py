"""Formulário de lançamento de ocorrências de avaria (módulo BOA).

Uma ocorrência pode envolver vários produtos (mesmo motivo, turno, conferente etc.).
Os campos da ocorrência são preenchidos uma vez; os produtos são digitados em uma
tabela editável e todos são registrados juntos ao clicar em "Registrar Ocorrência".
"""

import streamlit as st
from datetime import date

from data.cadastros import buscar_nome_produto, carregar_lista
from data.queries import salvar_registro

_OPCAO_VAZIA = "— selecionar —"
_OPCAO_OUTRO = "Outro (digitar)"

_PREFIXOS_PARA_LIMPAR = ("f_", "qtd_item_", "remover_item_")


def _campo_selecao(label, opcoes, key, obrigatorio=True, valor_padrao=None):
    lista = ([] if valor_padrao else [_OPCAO_VAZIA]) + opcoes + [_OPCAO_OUTRO]
    indice = lista.index(valor_padrao) if valor_padrao in lista else 0
    marcador = " *" if obrigatorio else ""
    escolha = st.selectbox(f"{label}{marcador}", lista, index=indice, key=key)
    if escolha == _OPCAO_OUTRO:
        return st.text_input(f"Digite o valor para {label}", key=f"{key}_outro").strip().upper()
    if escolha == _OPCAO_VAZIA:
        return ""
    return escolha


def _limpar_formulario():
    st.session_state.itens_produtos = []
    for k in list(st.session_state.keys()):
        if k.startswith(_PREFIXOS_PARA_LIMPAR):
            del st.session_state[k]


def _adicionar_produto():
    codigo = st.session_state.get("f_novo_codigo")
    if codigo is not None:
        st.session_state.setdefault("proximo_item_id", 0)
        item_id = st.session_state.proximo_item_id
        st.session_state.proximo_item_id += 1
        st.session_state.itens_produtos.append({"id": item_id, "codigo_produto": int(codigo), "quantidade": 1})
    st.session_state.f_novo_codigo = None


def formulario_registro():
    if "msg_sucesso" in st.session_state:
        st.success(st.session_state.pop("msg_sucesso"))

    st.markdown(
        "<div class='subtitle' style='margin-bottom:16px;'>"
        "Preencha os dados da ocorrência e adicione quantos produtos forem necessários "
        "na tabela abaixo antes de registrar. As listas deste formulário são as mesmas "
        "mantidas em <b>Cadastro</b>."
        "</div>",
        unsafe_allow_html=True,
    )

    revendas = carregar_lista("revenda")
    conferentes = carregar_lista("conferente")
    motivos = carregar_lista("motivo")
    placas = carregar_lista("placa")
    motoristas = carregar_lista("motorista")
    justificativas = carregar_lista("justificativa")
    areas = carregar_lista("area")
    responsaveis = carregar_lista("responsavel")
    funcoes = carregar_lista("funcao_colaborador")
    turnos = carregar_lista("turno")

    with st.container(border=True):
        st.markdown("<div class='section-title'>Dados da ocorrência</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            revenda = _campo_selecao("1. REVENDA", revendas, "f_revenda",
                                      valor_padrao=revendas[0] if len(revendas) == 1 else None)
        with col2:
            conferente = _campo_selecao("2. CONFERENTE", conferentes, "f_conferente")

        col1, col2 = st.columns(2)
        with col1:
            data_ocorrencia = st.date_input("3. DATA OCORRÊNCIA *", value=date.today(), format="DD/MM/YYYY", key="f_data")
        with col2:
            motivo = _campo_selecao("6. MOTIVO", motivos, "f_motivo")

        col1, col2 = st.columns(2)
        with col1:
            placa = _campo_selecao("7. PLACA", placas, "f_placa", obrigatorio=False)
        with col2:
            motorista = _campo_selecao("8. MOTORISTA", motoristas, "f_motorista", obrigatorio=False)

        justificativa = _campo_selecao("9. JUSTIFICATIVA DA AVARIA", justificativas, "f_justificativa")

        col1, col2 = st.columns(2)
        with col1:
            area = _campo_selecao("10. ÁREA", areas, "f_area")
        with col2:
            responsavel = _campo_selecao("11. RESPONSÁVEL", responsaveis, "f_responsavel", obrigatorio=False)

        col1, col2 = st.columns(2)
        with col1:
            funcao_colaborador = _campo_selecao("12. FUNÇÃO DO COLABORADOR", funcoes, "f_funcao", obrigatorio=False)
        with col2:
            turno = _campo_selecao("13. TURNO", turnos, "f_turno")

    if "itens_produtos" not in st.session_state:
        st.session_state.itens_produtos = []

    with st.container(border=True):
        st.markdown("<div class='section-title'>4-5. Produtos desta ocorrência</div>", unsafe_allow_html=True)
        st.caption("Digite o código do produto e pressione Enter. A referência aparece automaticamente na lista abaixo.")

        st.number_input(
            "Código do Produto", min_value=0, step=1, value=None, key="f_novo_codigo",
            on_change=_adicionar_produto, placeholder="Digite o código e pressione Enter",
            label_visibility="collapsed",
        )

        if st.session_state.itens_produtos:
            st.caption(f"{len(st.session_state.itens_produtos)} produto(s) adicionados:")
            cab1, cab2, cab3, _ = st.columns([1, 3, 1.2, 0.6])
            cab1.markdown("**Código**")
            cab2.markdown("**Referência**")
            cab3.markdown("**Quantidade**")
            for i, item in enumerate(st.session_state.itens_produtos):
                c1, c2, c3, c4 = st.columns([1, 3, 1.2, 0.6])
                c1.markdown(str(item["codigo_produto"]))
                c2.markdown(buscar_nome_produto(item["codigo_produto"]) or "_— não cadastrado —_")
                nova_qtd = c3.number_input("Qtd", min_value=1, step=1, value=item["quantidade"],
                                            key=f"qtd_item_{item['id']}", label_visibility="collapsed")
                st.session_state.itens_produtos[i]["quantidade"] = nova_qtd
                if c4.button("🗑️", key=f"remover_item_{item['id']}"):
                    st.session_state.itens_produtos.pop(i)
                    st.rerun()

    itens_validos = [item for item in st.session_state.itens_produtos if item["codigo_produto"] is not None]

    enviado = st.button("Registrar Ocorrência", type="primary")

    if not enviado:
        return

    faltando = []
    if not revenda: faltando.append("REVENDA")
    if not conferente: faltando.append("CONFERENTE")
    if not motivo: faltando.append("MOTIVO")
    if not justificativa: faltando.append("JUSTIFICATIVA DA AVARIA")
    if not area: faltando.append("ÁREA")
    if not turno: faltando.append("TURNO")

    if faltando:
        st.error("Preencha os campos obrigatórios: " + ", ".join(faltando))
        return

    if not itens_validos:
        st.error("Adicione ao menos um produto.")
        return

    dados_comuns = {
        "revenda": revenda,
        "conferente": conferente,
        "data_ocorrencia": data_ocorrencia.isoformat(),
        "motivo": motivo,
        "placa": placa,
        "motorista": motorista,
        "justificativa": justificativa,
        "area": area,
        "responsavel": responsavel,
        "funcao_colaborador": funcao_colaborador,
        "turno": turno,
    }

    ids_gerados = []
    for item in itens_validos:
        novo_id = salvar_registro({
            **dados_comuns,
            "codigo_produto": int(item["codigo_produto"]),
            "quantidade": int(item["quantidade"]),
        })
        ids_gerados.append(novo_id)

    st.session_state["msg_sucesso"] = (
        f"{len(ids_gerados)} ocorrência(s) registrada(s) com sucesso (IDs {ids_gerados[0]}–{ids_gerados[-1]}). "
        "Os indicadores do Dashboard já foram atualizados."
    )
    _limpar_formulario()
    st.rerun()
