# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Estado atual

Projeto implementado em Python 3.14 com **Poetry**, layout `src/`. O agente
multi-agente usa **Google ADK** (LiteLLM → Claude por padrão; Ollama como
alternativa offline), com interface **Chainlit**, CLI e notebook de entrega.

Comandos (use o venv do Poetry):

```powershell
poetry install                       # núcleo + dev + notebook
poetry install --with sentiment      # adiciona FinBERT-PT-BR (torch + transformers)
poetry run pytest                    # testes (sem rede)
poetry run ruff check .              # lint
poetry run ruff format .             # formatação
poetry run chainlit run app.py -w    # interface conversacional
poetry run assistente "..."          # CLI (uma pergunta) ou sem args (REPL)
```

Estrutura: `src/assistente/` com `config.py`, `schemas.py` (`StockAnalysis`),
`runner.py` (ADK Runner + SessionService), `cli.py`, `backtest.py`, `agents/`
(technical, news, orchestrator) e `tools/` (market_data, indicators, news,
sentiment, recommendation, charting). UI em `app.py`; demo em `notebooks/demo.ipynb`.

Notas de implementação relevantes:
- Tickers da B3 recebem sufixo `.SA` para o yfinance (`to_yahoo_symbol`).
- Indicadores usam `pandas-ta-classic` (import `pandas_ta_classic`), pois o
  `pandas-ta` original está em arquivamento.
- O sentimento é uma tool isolada e opcional; degrada com elegância
  (`sentiment_available=False`) se torch/transformers/modelo não estiverem presentes.
- O backtest é determinístico (não chama o LLM), com indicadores causais.
- A decisão final do orquestrador exige `ANTHROPIC_API_KEY` (ou Ollama); as
  demais tools funcionam sem credenciais.

## O que este projeto deve ser

Trabalho final de *Intelligent Multi Agents* (MBA FIAP, turma 11DTS). O objetivo
é um **Assistente de Investimentos** em renda variável construído como AI Agent
em Python, que recomenda de forma autônoma e explicável `COMPRAR` / `VENDER` /
`AGUARDAR` para um conjunto fixo de ações da B3: `VALE3`, `PETR4`, `BBAS3` e
`ITUB4`. A especificação completa está em
`docs/descritivo/Projeto_Integrado_AI_Agents_v2.pdf` — leia antes de planejar
qualquer implementação.

O agente combina duas fontes de sinal e raciocina sobre elas antes de decidir:
notícias financeiras com análise de sentimento (NLP/LLM) e indicadores técnicos
de análise gráfica (RSI, MACD, SMA/EMA, Bandas de Bollinger, volume).

## Arquitetura pretendida

O fluxo segue o ciclo **Percepção → Raciocínio → Ação** com estratégia **ReAct
(Reasoning + Acting)**, registrando o Chain-of-Thought de cada decisão:

1. Coleta de dados — preços/volumes via `yfinance` (OHLCV, sem API key) e
   notícias via `feedparser` sobre RSS feeds (InfoMoney, B3, Reuters, Valor).
2. Processamento — cálculo dos indicadores técnicos (sugerido `pandas-ta` ou
   `TA-Lib`) e classificação de sentimento das notícias (Positivo/Negativo/
   Neutro) com score de impacto por ticker.
3. Análise pelo LLM Agent — raciocínio passo a passo sobre os sinais agregados.
4. Recomendação — decisão + justificativa em linguagem natural.

O agente é orientado a **tools**; o descritivo exige pelo menos 3 ferramentas e
sugere esta assinatura como referência:
`search_news(ticker)`, `get_price_data(ticker, period)`,
`calculate_indicators(data)`, `generate_recommendation(analysis)`.

Estrutura de dado esperada por ação/dia de análise:

```json
{ "ticker": "VALE3", "date": "2024-11-15", "close": 61.42, "rsi": 45.2,
  "macd_signal": "bullish", "news_sentiment": 0.72, "recommendation": "COMPRAR" }
```

Extensão multi-agente é valorizada e prevista no descritivo: agente de notícias
+ agente técnico + agente orquestrador que toma a decisão final.

## Stack sugerida pelo descritivo

São sugestões do enunciado, não decisões já tomadas — confirme a escolha antes
de fixar dependências.

- Framework de agentes: LangChain, LangGraph ou Google ADK (há material de apoio
  de ADK em `docs/apoio/`).
- LLM: OpenAI GPT-4o ou Anthropic Claude (exigem API key paga); alternativa
  gratuita e local é Llama 3 via Ollama.
- Dados de mercado: `yfinance`. Notícias: `feedparser`. Indicadores:
  `pandas-ta` / `TA-Lib` / `mplfinance`. Sentimento (opcional): FinBERT
  (HuggingFace `transformers`), VADER ou spaCy. Visualização: Plotly /
  Matplotlib (expostos como tool do agente).

Entrega esperada como Jupyter Notebook ou repositório GitHub. A avaliação cobra
acurácia das recomendações (acerto de tendência vs. comportamento real no
período de teste) e qualidade do Chain-of-Thought; backtest contra Buy-and-Hold
e interface conversacional são opcionais, mas valorizados.

## Convenções

- Chaves de API e tokens nunca entram no código nem no Git — use variáveis de
  ambiente (`.env` fora do versionamento). O design deve permitir rodar
  totalmente offline/local com Ollama, sem credenciais pagas.
- O raciocínio que leva a cada recomendação deve ser registrado de forma
  explícita e legível — é critério de avaliação, não detalhe de implementação.
