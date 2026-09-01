# StockFlow — Gestão de Armazém

Dashboard e formulários de gestão de armazém (Boletim de Ocorrência de Avaria e
Recebimento), construído em Streamlit com dados no Supabase.

## Rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

Crie `.streamlit/secrets.toml` com:

```toml
SUPABASE_URL = "https://SEU-PROJETO.supabase.co"
SUPABASE_SERVICE_KEY = "sua-service-role-key"
```

## Estrutura

- `app.py` — roteador de UI (sidebar, navegação, filtros)
- `config.py` — cores, metas, regras de status
- `data/` — leitura e escrita no Supabase (ocorrências, cadastros, recebimento)
- `ui/` — componentes de página (dashboard, formulário BOA, cadastro, recebimento)
