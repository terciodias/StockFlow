"""Cores corporativas, metas e regras de status. Ajuste os valores aqui — nenhum outro
arquivo deve conter cor, meta ou limiar de status hardcoded."""

CORES = {
    "primaria": "#2F6FED",
    "secundaria": "#1B2A57",
    "sidebar": "#101B3D",
    "sidebar_hover": "#1C2C5C",
    "ok": "#1CB855",
    "atencao": "#F5A623",
    "critico": "#E5484D",
    "meta": "#9AA5B1",
    "neutro": "#6B6B6B",
    "texto": "#1A1A1A",
    "fundo_card": "#FFFFFF",
    "borda_card": "#ECECEC",
    "paleta_categorica": [
        "#2F6FED", "#1CB855", "#F5A623", "#9B51E0",
        "#E5484D", "#17A2B8", "#6B6B6B", "#C77DFF",
    ],
}

# Status possíveis de uma conferência de recebimento (fluxo fixo, não é cadastro dinâmico).
STATUS_CONFERENCIA = ["Pendente", "Em Conferência", "Concluído"]

# Nomes de exibição de cada lista dinâmica (dados ficam em stockflow_listas no Supabase,
# uma linha por campo/valor — ver data/cadastros.py).
NOMES_LISTAS_CADASTRAVEIS = {
    "revenda": "Revenda", "conferente": "Conferente", "motivo": "Motivo",
    "placa": "Placa", "motorista": "Motorista", "justificativa": "Justificativa da Avaria",
    "area": "Área", "responsavel": "Responsável", "funcao_colaborador": "Função do Colaborador",
    "turno": "Turno", "fornecedor": "Fornecedor", "transportadora": "Transportadora",
}

# Motivos são agrupados em duas famílias de causa-raiz para leitura gerencial.
MOTIVOS_AVARIA_PRODUTO = [
    "FURADA", "QUEBRADA", "MICRO FURO", "AMASSADA", "VAZADA",
    "ESTUFADA", "MAL CHEIO", "SEM RÓTULO", "SEM TAMPA", "PERDA POR SHELF",
]
MOTIVOS_FALTA = [
    "FALTA NA ENTREGA", "FALTA NO CARREGAMENTO", "FALTA DE FÁBRICA", "FALTA",
]

# --- Metas (ajustáveis conforme meta de negócio real) ---
# Ocorrências e quantidade: meta = média histórica mensal (queremos ficar abaixo dela).
# Concentração por turno: turnos equilibrados indicam processo estável; meta de referência 40%.
# Avaria de produto (evitável) vs falta: meta manter avaria de produto abaixo de 70% do total.
META_TURNO_CONCENTRACAO = 0.40
META_AVARIA_PRODUTO_PCT = 0.70
TOLERANCIA_AMARELO = 0.10  # até 10% acima da meta = amarelo; acima disso = vermelho

# Severidade de quantidade avariada por ocorrência (linhas da tabela de drill-down)
LIMIAR_QTD_CRITICO = 20
LIMIAR_QTD_ATENCAO = 8
