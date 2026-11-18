# MAF Workshop — Agentes com Microsoft Agent Framework, ViaCEP e PostgreSQL

Material de apoio da palestra *"Por onde começar criando agentes de IA com o
Microsoft Agent Framework"*. Cada arquivo em `agents/` corresponde a uma etapa
do storytelling; `index.html` é a página interativa com os modelos de
orquestração e os cenários.

```
maf-workshop/
├── index.html                       # página interativa (abra no navegador)
├── docker-compose.yml               # Postgres 16 já com schema + carga
├── requirements.txt
├── .env.example
├── PASSO_A_PASSO.md                 # preparação + como executar cada agente (terminal e DevUI)
├── PROMPTS.md                       # prompts para testar cada agente/workflow (DevUI ou terminal)
├── sql/
│   ├── 01_schema.sql                # tabelas, view, trigger, log de agentes
│   └── 02_seed.sql                  # 12 clientes, 12 endereços, 16 pedidos
├── scripts/
│   └── setup_db.py                  # alternativa ao docker (Postgres existente)
├── tools/
│   ├── viacep.py                    # consultar_cep  (httpx → viacep.com.br)
│   └── postgres.py                  # buscar_cliente, listar_pedidos, atualizar_endereco, relatorio_por_uf, log
└── agents/
    ├── _common.py                   # get_client(): foundry | azure-openai | openai
    ├── 01_hello_agent.py            # Etapa 1 · hello world
    ├── 02_agent_tools.py            # Etapa 2 · agente + tools
    ├── 03_sequential_atualizacao_cadastral.py   # Etapa 5 · SEQUENCIAL (ViaCEP → Postgres → resposta)
    ├── 04_sequential_relatorio_regional.py      # Etapa 5 · SEQUENCIAL analítico + workflow-as-agent
    ├── 05_handoff_atendimento.py    # Etapa 5 · HANDOFF (triagem → especialista)
    ├── 06_concurrent_analise.py     # Etapa 5 · CONCORRENTE (3 análises em paralelo)
    ├── 07_observability.py          # Etapa 6 · traces no Foundry / Aspire / console
    └── devui_app.py                 # DevUI: todos os agentes e workflows numa interface web
```

## 1. Banco de dados

**Com Docker (recomendado para a demo):**

```bash
docker compose up -d
# os scripts em sql/ rodam automaticamente na primeira subida
docker compose exec postgres psql -U maf -d workshop -c "SELECT * FROM workshop.vw_cliente_resumo LIMIT 3;"
```

**Em um Postgres existente (local, Azure Database for PostgreSQL…):**

```bash
cp .env.example .env            # ajuste DATABASE_URL
pip install -r requirements.txt
python scripts/setup_db.py      # --reset para recriar do zero
```

## 2. Modelo

Implante um modelo em um projeto do **Microsoft Foundry** (ex.: `gpt-4o-mini`) e preencha
`FOUNDRY_PROJECT_ENDPOINT` e `FOUNDRY_MODEL` no `.env`. Faça `az login` — os exemplos usam
`AzureCliCredential`.

Para mostrar a flexibilidade na hora: mude `MODEL_PROVIDER` para `azure-openai` ou
`openai` (inclusive Ollama local via `OPENAI_BASE_URL`). Nenhum agente muda.

## 3. Rodando os exemplos

```bash
cd agents
python 01_hello_agent.py
python 02_agent_tools.py
python 03_sequential_atualizacao_cadastral.py
python 04_sequential_relatorio_regional.py
python 05_handoff_atendimento.py
python 06_concurrent_analise.py
OBS_TARGET=foundry python 07_observability.py     # ou azure-monitor | aspire | console
```

No PowerShell: `$env:OBS_TARGET="azure-monitor"; python 07_observability.py` (ou defina `OBS_TARGET` no `.env`).

### DevUI (interface web)

```bash
cd agents
python devui_app.py        # abre http://localhost:8080 (porta: DEVUI_PORT; sem navegador: DEVUI_OPEN=0)
```

Registra os 6 agentes/workflows (`HelloAgent`, `AtendenteCadastro`, `atualizacao_cadastral`,
`relatorio_regional`, `atendimento_handoff`, `analise_concorrente`) usando as mesmas funções
`build_agent` / `build_workflow` dos exemplos. Mostra o grafo dos workflows, as chamadas de tools
e a aba **Traces**; com `OBS_TARGET=azure-monitor`/`foundry` os mesmos spans vão para o App Insights.
Prompts prontos para cada um em [`PROMPTS.md`](PROMPTS.md).

Teste rápido das tools sem LLM:

```bash
python -m tools.viacep          # consulta 01310-100 no ViaCEP
```

## 4. Observabilidade

| OBS_TARGET | Onde ver | Pré-requisito |
|---|---|---|
| `console` | terminal | nenhum |
| `aspire` | http://localhost:18888 | `docker run --rm -d -p 18888:18888 -p 4317:18889 mcr.microsoft.com/dotnet/aspire-dashboard:latest` |
| `azure-monitor` | Portal ▸ Application Insights ▸ Transaction search / Agents (preview) | `APPLICATIONINSIGHTS_CONNECTION_STRING` no `.env` (qualquer `MODEL_PROVIDER`) |
| `foundry` | Foundry ▸ Build ▸ Agents ▸ Traces (e Monitor) | Application Insights conectado ao projeto (ou a connection string no `.env`) |

Com `foundry` ou `azure-monitor`, **todos os exemplos (01–07)** enviam traces, métricas e logs ao
Application Insights: cada execução vira uma operação (span `demo.<script>`) com os spans de workflow,
agentes (`invoke_agent`), tools (`execute_tool`) e chamadas ao modelo (`chat …`, com prompts e tokens).
Os scripts imprimem o `operation_Id` ao final; para achar a execução:
`dependencies | where operation_Id == "<id>"`. A ingestão leva de 1 a 3 minutos.
Se a telemetria não puder ser ligada (ex.: connection string ausente), as demos 01–06 seguem sem ela.

## Cenários cobertos

| Cenário | Orquestração | Tools | Arquivo |
|---|---|---|---|
| Atualização cadastral com validação de CEP | Sequencial | ViaCEP, Postgres (R/W) | `03_…` |
| Relatório de pedidos por região | Sequencial (workflow-as-agent) | Postgres (R) | `04_…` |
| Atendimento com triagem | Handoff | ViaCEP, Postgres | `05_…` |
| Análise de risco/oportunidade | Concorrente | Postgres (R) | `06_…` |

> Dados 100 % fictícios. CPFs e e-mails inventados.
e mo