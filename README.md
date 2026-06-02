# Assistente de Investimentos (B3)

Trabalho final de *Intelligent Multi Agents* (MBA FIAP, turma 11DTS).

AI Agent **multi-agente** construído com **Google ADK** que recomenda de forma
autônoma e explicável `COMPRAR` / `VENDER` / `AGUARDAR` para as ações `VALE3`,
`PETR4`, `BBAS3` e `ITUB4`, combinando **análise técnica** (indicadores gráficos)
e **sentimento de notícias** (FinBERT-PT-BR), com raciocínio passo a passo
(estratégia ReAct / Chain-of-Thought).

## Arquitetura

Ciclo Percepção → Raciocínio → Ação, com três agentes:

- `technical_agent` — interpreta RSI, MACD, SMA/EMA, Bandas de Bollinger e volume.
- `news_agent` — coleta notícias (RSS) e avalia o sentimento com FinBERT-PT-BR.
- `investment_orchestrator` (root) — consulta os dois agentes acima (via `AgentTool`),
  obtém um score quantitativo baseline (`generate_recommendation`) e decide,
  registrando o raciocínio.

```
src/assistente/
├── config.py        # Settings (.env), tickers, feeds RSS
├── schemas.py       # StockAnalysis (formato do descritivo)
├── runner.py        # ADK Runner + SessionService (stream de eventos)
├── cli.py           # CLI / REPL
├── backtest.py      # acurácia + Buy-and-Hold (motor determinístico)
├── agents/          # technical, news, orchestrator
└── tools/           # market_data, indicators, news, sentiment, recommendation, charting
app.py               # interface Chainlit
notebooks/demo.ipynb # entrega Jupyter
```

## Stack

Python 3.14 · Google ADK · LiteLLM (Claude por padrão) · yfinance · feedparser ·
pandas-ta-classic · FinBERT-PT-BR (transformers + torch CPU) · Chainlit ·
mplfinance/Plotly · Pydantic. Gerenciado com **Poetry**.

## Pré-requisitos

- Python 3.14 (o projeto também roda em 3.12/3.13 — ver Solução de problemas).
- [Poetry](https://python-poetry.org/): `pipx install poetry`.

## Setup

```powershell
# 1. Dependências (núcleo + dev + notebook)
poetry install

# 2. Sentimento dedicado (FinBERT-PT-BR: baixa torch + transformers, ~CPU)
poetry install --with sentiment

# 3. Credenciais
copy .env.example .env   # depois edite o .env
```

No `.env`, defina a chave da Anthropic (padrão Claude):

```
ADK_MODEL=anthropic/claude-sonnet-4-5
ANTHROPIC_API_KEY=<sua-chave>
```

> Confirme o identificador atual do modelo Claude na documentação da Anthropic.
> Para rodar **offline/sem chave paga**, suba o [Ollama](https://ollama.com/) e use
> `ADK_MODEL=ollama_chat/llama3` (+ `OLLAMA_API_BASE=http://localhost:11434`).

## Como executar

```powershell
# Interface conversacional (recomendado)
poetry run chainlit run app.py -w

# CLI: uma pergunta
poetry run assistente "Por que comprar PETR4 hoje?"

# CLI: modo interativo
poetry run assistente

# Notebook de demonstração / entrega
poetry run jupyter lab notebooks/demo.ipynb
```

As tools de dados (preço, indicadores, notícias, sentimento, backtest) funcionam
**sem** chave de API. A decisão final do agente orquestrador exige o LLM
(`ANTHROPIC_API_KEY` ou Ollama).

## Avaliação

- **Acurácia** (acerto de tendência) e **Backtest vs Buy-and-Hold**:
  `assistente.backtest.run_backtest_all(...)` ou a seção 4 do notebook.
- **Chain-of-Thought**: visível no stream do Chainlit e na CLI (chamadas de tools
  + justificativa final).

O backtest usa o motor determinístico (mesmo baseline do orquestrador), com
indicadores causais (sem lookahead). O sentimento histórico não está disponível,
então o backtest é técnico (sentimento = 0) — limitação explícita.

## Testes e qualidade

```powershell
poetry run pytest        # testes (sem rede): indicadores, recomendação, schemas
poetry run ruff check .  # lint
poetry run ruff format . # formatação
```

## Solução de problemas

- **Falha ao instalar no Python 3.14**: recrie o ambiente em 3.12 sem mudar código:
  `poetry env use 3.12 && poetry install --with sentiment`.
- **FinBERT-PT-BR indisponível**: o agente continua funcionando e avalia o
  sentimento pelas manchetes via LLM; o campo `sentiment_available` indica o modo.

## Aviso

Projeto educacional. As recomendações são geradas automaticamente e **não**
constituem recomendação formal de investimento.
