"""Conferência de recebimento: registra a chegada de uma carga (NF, fornecedor,
transportadora) e a conferência produto a produto (pedido x recebido x avariado).
Um produto avariado aqui gera automaticamente uma ocorrência ligada no BOA."""

from datetime import date, datetime

import streamlit as st

from config import STATUS_CONFERENCIA
from data.cadastros import buscar_nome_produto, carregar_lista
from data.queries import salvar_registro
from data.recebimento import carregar_recebimentos, proximo_id_recebimento, salvar_item_recebimento

_OPCAO_VAZIA = "— selecionar —"
_OPCAO_OUTRO = "Outro (digitar)"

_PREFIXOS_PARA_LIMPAR = ("r_", "rqtd_", "rmot_", "rremover_")


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
    st.session_state.itens_recebimento = []
    for k in list(st.session_state.keys()):
        if k.startswith(_PREFIXOS_PARA_LIMPAR):
            del st.session_state[k]


def _adicionar_produto():
    codigo = st.session_state.get("r_novo_codigo")
    if codigo is not None:
        st.session_state.setdefault("proximo_item_recebimento_id", 0)
        item_id = st.session_state.proximo_item_recebimento_id
        st.session_state.proximo_item_recebimento_id += 1
        st.session_state.itens_recebimento.append({
            "id": item_id, "codigo_produto": int(codigo),
            "quantidade_pedida": 0, "quantidade_recebida": 0,
            "quantidade_avariada": 0, "observacao_item": "",
        })
    st.session_state.r_novo_codigo = None


def pagina_recebimento():
    _formulario_recebimento()
    _tabela_historico()


def _formulario_recebimento():
    if "msg_sucesso_recebimento" in st.session_state:
        st.success(st.session_state.pop("msg_sucesso_recebimento"))

    st.markdown(
        "<div class='subtitle' style='margin-bottom:16px;'>"
        "Registre a chegada da carga uma vez e confira quantos produtos forem necessários "
        "antes de concluir. Produtos com avaria geram automaticamente uma ocorrência no BOA."
        "</div>",
        unsafe_allow_html=True,
    )

    revendas = carregar_lista("revenda")
    fornecedores = carregar_lista("fornecedor")
    transportadoras = carregar_lista("transportadora")
    placas = carregar_lista("placa")
    motoristas = carregar_lista("motorista")
    conferentes = carregar_lista("conferente")
    turnos = carregar_lista("turno")
    motivos = carregar_lista("motivo")

    with st.container(border=True):
        st.markdown("<div class='section-title'>Chegada da carga</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            revenda = _campo_selecao("Revenda", revendas, "r_revenda",
                                      valor_padrao=revendas[0] if len(revendas) == 1 else None)
        with col2:
            numero_nf = st.text_input("Número da NF *", key="r_nf")

        col1, col2 = st.columns(2)
        with col1:
            fornecedor = _campo_selecao("Fornecedor", fornecedores, "r_fornecedor")
        with col2:
            transportadora = _campo_selecao("Transportadora", transportadoras, "r_transportadora", obrigatorio=False)

        col1, col2 = st.columns(2)
        with col1:
            placa = _campo_selecao("Placa", placas, "r_placa", obrigatorio=False)
        with col2:
            motorista = _campo_selecao("Motorista", motoristas, "r_motorista", obrigatorio=False)

        col1, col2 = st.columns(2)
        with col1:
            data_chegada = st.date_input("Data de chegada *", value=date.today(), format="DD/MM/YYYY", key="r_data")
        with col2:
            hora_chegada = st.time_input("Hora de chegada *", value=datetime.now().time().replace(second=0, microsecond=0), key="r_hora")

        col1, col2 = st.columns(2)
        with col1:
            conferente = _campo_selecao("Conferente", conferentes, "r_conferente")
        with col2:
            turno = _campo_selecao("Turno", turnos, "r_turno")

        status_conferencia = st.selectbox("Status da conferência *", STATUS_CONFERENCIA, key="r_status")
        observacoes_gerais = st.text_area("Observações gerais", key="r_obs", placeholder="Opcional")

    if "itens_recebimento" not in st.session_state:
        st.session_state.itens_recebimento = []

    with st.container(border=True):
        st.markdown("<div class='section-title'>Conferência por produto</div>", unsafe_allow_html=True)
        st.caption("Digite o código do produto e pressione Enter. Informe a quantidade pedida, recebida e — se houver — avariada.")

        st.number_input(
            "Código do Produto", min_value=0, step=1, value=None, key="r_novo_codigo",
            on_change=_adicionar_produto, placeholder="Digite o código e pressione Enter",
            label_visibility="collapsed",
        )

        for i, item in enumerate(st.session_state.itens_recebimento):
            with st.container(border=True):
                c1, c2 = st.columns([1, 4])
                c1.markdown(f"**Código {item['codigo_produto']}**")
                c2.markdown(buscar_nome_produto(item["codigo_produto"]) or "_— não cadastrado —_")

                c1, c2, c3, c4 = st.columns([1, 1, 1, 0.5])
                pedida = c1.number_input("Qtd Pedida", min_value=0, step=1, value=item["quantidade_pedida"],
                                          key=f"rqtd_pedida_{item['id']}")
                recebida = c2.number_input("Qtd Recebida", min_value=0, step=1, value=item["quantidade_recebida"],
                                            key=f"rqtd_recebida_{item['id']}")
                avariada = c3.number_input("Qtd Avariada", min_value=0, step=1, value=item["quantidade_avariada"],
                                            key=f"rqtd_avariada_{item['id']}")
                if c4.button("🗑️", key=f"rremover_item_{item['id']}"):
                    st.session_state.itens_recebimento.pop(i)
                    st.rerun()

                st.session_state.itens_recebimento[i].update({
                    "quantidade_pedida": pedida, "quantidade_recebida": recebida, "quantidade_avariada": avariada,
                })

                diferenca = recebida - pedida
                if diferenca < 0:
                    st.caption(f"🔴 Falta de {abs(diferenca)} unidade(s) em relação ao pedido.")
                elif diferenca > 0:
                    st.caption(f"🟡 Sobra de {diferenca} unidade(s) em relação ao pedido.")
                else:
                    st.caption("✅ Quantidade recebida confere com o pedido.")

                motivo_avaria = ""
                if avariada > 0:
                    motivo_avaria = _campo_selecao("Motivo da avaria", motivos, f"rmot_{item['id']}")
                    st.session_state.itens_recebimento[i]["motivo_avaria"] = motivo_avaria

    itens_validos = [item for item in st.session_state.itens_recebimento if item["codigo_produto"] is not None]

    enviado = st.button("Registrar Recebimento", type="primary")

    if not enviado:
        return

    faltando = []
    if not revenda: faltando.append("REVENDA")
    if not numero_nf.strip(): faltando.append("NÚMERO DA NF")
    if not fornecedor: faltando.append("FORNECEDOR")
    if not conferente: faltando.append("CONFERENTE")
    if not turno: faltando.append("TURNO")

    if faltando:
        st.error("Preencha os campos obrigatórios: " + ", ".join(faltando))
        return

    if not itens_validos:
        st.error("Adicione ao menos um produto na conferência.")
        return

    itens_sem_motivo = [i for i in itens_validos if i["quantidade_avariada"] > 0 and not i.get("motivo_avaria")]
    if itens_sem_motivo:
        st.error("Selecione o motivo da avaria para todo produto com quantidade avariada informada.")
        return

    data_hora_chegada = datetime.combine(data_chegada, hora_chegada).isoformat()
    id_receb = proximo_id_recebimento()

    dados_comuns = {
        "id_recebimento": id_receb,
        "data_hora_chegada": data_hora_chegada,
        "revenda": revenda,
        "numero_nf": numero_nf.strip(),
        "fornecedor": fornecedor,
        "transportadora": transportadora,
        "placa": placa,
        "motorista": motorista,
        "conferente": conferente,
        "turno": turno,
        "status_conferencia": status_conferencia,
        "observacoes_gerais": observacoes_gerais,
    }

    ids_gerados = []
    ocorrencias_boa_geradas = []
    for item in itens_validos:
        id_ocorrencia_boa = ""
        if item["quantidade_avariada"] > 0:
            id_ocorrencia_boa = salvar_registro({
                "revenda": revenda, "conferente": conferente, "data_ocorrencia": data_chegada.isoformat(),
                "codigo_produto": int(item["codigo_produto"]), "quantidade": int(item["quantidade_avariada"]),
                "motivo": item.get("motivo_avaria", ""), "placa": placa, "motorista": motorista,
                "justificativa": "AVARIA IDENTIFICADA NO RECEBIMENTO", "area": "Recebimento",
                "responsavel": "", "funcao_colaborador": "", "turno": turno,
            })
            ocorrencias_boa_geradas.append(id_ocorrencia_boa)

        novo_id = salvar_item_recebimento({
            **dados_comuns,
            "codigo_produto": int(item["codigo_produto"]),
            "quantidade_pedida": int(item["quantidade_pedida"]),
            "quantidade_recebida": int(item["quantidade_recebida"]),
            "diferenca": int(item["quantidade_recebida"]) - int(item["quantidade_pedida"]),
            "quantidade_avariada": int(item["quantidade_avariada"]),
            "motivo_avaria": item.get("motivo_avaria", ""),
            "observacao_item": item.get("observacao_item", ""),
            "id_ocorrencia_boa": id_ocorrencia_boa,
        })
        ids_gerados.append(novo_id)

    msg = f"Recebimento #{id_receb} registrado com {len(ids_gerados)} produto(s)."
    if ocorrencias_boa_geradas:
        msg += f" {len(ocorrencias_boa_geradas)} ocorrência(s) de avaria gerada(s) automaticamente no BOA."
    st.session_state["msg_sucesso_recebimento"] = msg
    _limpar_formulario()
    st.rerun()


def _tabela_historico():
    df = carregar_recebimentos()
    if df.empty:
        return

    st.markdown("<div class='section-title' style='margin-top:8px;'>Últimos recebimentos</div>", unsafe_allow_html=True)
    resumo = (
        df.groupby("id_recebimento")
        .agg(
            data_hora_chegada=("data_hora_chegada", "first"), numero_nf=("numero_nf", "first"),
            fornecedor=("fornecedor", "first"), transportadora=("transportadora", "first"),
            conferente=("conferente", "first"), status_conferencia=("status_conferencia", "first"),
            produtos=("codigo_produto", "count"), unidades_avariadas=("quantidade_avariada", "sum"),
        )
        .reset_index()
        .sort_values("data_hora_chegada", ascending=False)
        .head(20)
    )
    resumo = resumo.rename(columns={
        "id_recebimento": "Recebimento #", "data_hora_chegada": "Chegada", "numero_nf": "NF",
        "fornecedor": "Fornecedor", "transportadora": "Transportadora", "conferente": "Conferente",
        "status_conferencia": "Status", "produtos": "Produtos", "unidades_avariadas": "Unid. Avariadas",
    })
    with st.container(border=True):
        st.dataframe(resumo, hide_index=True, width="stretch")
