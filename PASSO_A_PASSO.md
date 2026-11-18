# Passo a passo: como executar cada agente

Guia para rodar o workshop do zero no Windows (PowerShell). Para os prompts de teste de cada
agente, veja [`PROMPTS.md`](PROMPTS.md).

---

## Parte 1 · Preparação (uma vez)

### 1. Pré-requisitos

| O quê | Para quê | Como conferir |
|---|---|---|
| Python 3.12 | rodar os agentes | `py -3.12 --version` |
| Docker Desktop (aberto) | banco PostgreSQL da demo | `docker ps` |
| Azure CLI | autenticar no Foundry (`AzureCliCredential`) | `az --version` |
| Acesso ao projeto Foundry | modelo usado pelos agentes | ver o passo 4 |

### 2. Ambiente Python

Crie o ambiente **fora do OneDrive**, senão ele sincroniza milhares de arquivos:

```powershell
py -3.12 -m venv C:\venvs\maf
C:\venvs\maf\Scripts\Activate.ps1
cd "C:\Users\<você>\OneDrive\Palestras\Palestra-Fernando\maf-workshop\maf-workshop"
pip install -r requirements.txt
```

> Em todo terminal novo, ative de novo com `C:\venvs\maf\Scripts\Activate.ps1`.
> O prompt passa a mostrar `(maf)`.

### 3. Arquivo `.env`

Na raiz do projeto (copie de `.env.example` se não existir):

| Variável | Valor |
|---|---|
| `MODEL_PROVIDER` | `foundry` |
| `FOUNDRY_PROJECT_ENDPOINT` | Foundry ▸ projeto ▸ Overview ▸ endpoint do projeto |
| `FOUNDRY_MODEL` | nome do **deployment** do modelo no projeto |
| `DATABASE_URL` | `postgresql://maf:maf@localhost:5432/workshop` (padrão do docker) |
| `OBS_TARGET` | `azure-monitor` (envia tudo ao App Insights) · `console` · `none` |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | App Insights ▸ Overview ▸ Connection String (para `azure-monitor`) |

### 4. Login no Azure

Entre com **a conta onde está o projeto Foundry**:

```powershell
az login                       # se a conta tiver vários diretórios: az login --tenant <id>
az account show --query "{conta:user.name, assinatura:name}" -o table
```

### 5. Banco de dados

```powershell
docker compose up -d
docker compose exec postgres psql -U maf -d workshop -c "SELECT nome, cidade, uf FROM workshop.vw_cliente_resumo LIMIT 3;"
```

Os scripts em `sql/` rodam sozinhos na primeira subida (12 clientes, 16 pedidos).

### 6. Teste rápido, sem modelo

```powershell
python -m tools.viacep          # deve imprimir o endereço da Av. Paulista (CEP 01310-100)
```

Um `RuntimeWarning: 'tools.viacep' found in sys.modules...` pode aparecer antes do resultado; é inofensivo.

Se os passos 1 a 6 passaram, está tudo pronto.

---

## Parte 2 · Executando cada agente (terminal)

Todos os comandos rodam de dentro da pasta `agents`:

```powershell
cd agents
```

Com `OBS_TARGET=azure-monitor`, cada script termina com uma linha
`📡 telemetria → … · operation_Id <id>`. Use esse id para achar a execução no App Insights
([como](PROMPTS.md#conferir-no-application-insights)).

### 01 · Hello Agent: o menor agente possível

```powershell
python 01_hello_agent.py
```

- **O que acontece:** um agente só com instruções ("responda em no máximo 2 frases"), sem tools.
- **Saída esperada:** uma explicação curta do que é um agente de IA.
- **Grava no banco?** Não.

### 02 · Agente com tools: ViaCEP + Postgres

```powershell
python 02_agent_tools.py
```

- **O que acontece:** o agente decide sozinho quando chamar `consultar_cep`, `buscar_cliente_por_cpf` e `listar_pedidos_cliente`.
- **Saída esperada:** duas perguntas respondidas:
  1. o endereço da Ana (Av. Paulista, 1578) e o pedido em aberto PED-2026-0001 (Notebook, enviado);
  2. o CEP 04538-132 é da Av. Brig. Faria Lima, Itaim Bibi, São Paulo/SP.
- **Grava no banco?** Não (as tools são só de leitura).

### 03 · Sequencial: atualização cadastral ✏️

```powershell
python 03_sequential_atualizacao_cadastral.py
```

- **O que acontece:** três agentes em ordem. `validador_endereco` valida no ViaCEP, `analista_cadastro` grava no Postgres e `comunicador` escreve a resposta e o log.
- **Saída esperada:**
  - as etapas aparecem como `▶ validador_endereco`, `▶ analista_cadastro` e `▶ comunicador`;
  - o endereço da Ana é atualizado para a Av. Brig. Faria Lima, 3477;
  - vem um alerta de que o PED-2026-0001 já foi enviado para o endereço antigo.
- **Grava no banco?** Sim: um endereço novo da Ana (`origem = agente`) e duas linhas em `log_agentes`.
- ⚠️ A resposta sai em pedaços (uma linha `✔` por fragmento). É uma limitação conhecida da saída no terminal; no DevUI e no 07 ela sai inteira.

### 04 · Sequencial analítico: relatório por UF

```powershell
python 04_sequential_relatorio_regional.py
```

- **O que acontece:** `extrator` busca os dados por UF, `analista` interpreta e `redator` escreve o resumo executivo. O workflow inteiro é exposto como **um agente** (`workflow.as_agent`).
- **Saída esperada:** um relatório em markdown. PR lidera em valor (R$ 18.900,00) e SP lidera em volume (6 pedidos, R$ 13.485,80).
- **Grava no banco?** Não.
- ⚠️ No terminal aparece só o bloco `[redator]`, e o texto final pode sair repetido. No DevUI cada etapa aparece separada.

### 05 · Handoff: atendimento com triagem ✏️

```powershell
python 05_handoff_atendimento.py
```

- **O que acontece:** a `triagem` lê cada mensagem e transfere para `pedidos` ou para `cadastro`. São duas mensagens, cada uma um atendimento novo.
- **Saída esperada:**
  1. Elaine pergunta dos pedidos → `pedidos` responde PED-2026-0007 e 0008, enviados, previsão 23/10;
  2. Lucas muda de endereço → `cadastro` valida o CEP 01001-000 (Praça da Sé) e atualiza.
- **Grava no banco?** Sim: o endereço novo do Lucas.
- ⚠️ Está em modo autônomo: os agentes podem fazer vários turnos, e a saída é longa e sai em pedaços.

### 06 · Concorrente: três análises em paralelo

```powershell
python 06_concurrent_analise.py
```

- **O que acontece:** `risco_entrega`, `risco_cadastro` e `oportunidade` analisam o cliente João (CPF 012.345.678-90) **ao mesmo tempo**, e o resultado é consolidado.
- **Saída esperada:** as análises de `risco_entrega`, `risco_cadastro` e `oportunidade`, e depois `✔ CONSOLIDADO` (PED-2026-0013 enviado; cliente premium).
- **Grava no banco?** Não.
- ⚠️ No terminal, cada fragmento sai com o nome do agente (`[risco_entrega]` repetido muitas vezes). No DevUI cada agente é um item separado na Execution Timeline.

### 07 · Observabilidade: o mesmo fluxo do 03, instrumentado ✏️

```powershell
python 07_observability.py                                  # usa o OBS_TARGET do .env
$env:OBS_TARGET="console"; python 07_observability.py      # spans no terminal
Remove-Item Env:OBS_TARGET                                  # volta a usar o .env
```

- **O que acontece:** roda o pipeline sequencial para o Lucas (CEP 30130-010) dentro de um span `atendimento.atualizacao_cadastral`.
- **Saída esperada:** as etapas, a resposta final e duas linhas no fim: `Traces enviados para: …` e `operation_Id / trace id: <id>`.
- **Onde ver:** no App Insights (Transaction search, busque pelo id). Com `console`, os spans aparecem no próprio terminal. A ingestão no App Insights leva de 1 a 3 minutos.
- **Grava no banco?** Sim: o endereço novo do Lucas.

---

## Parte 3 · Executando pelo DevUI (interface web)

```powershell
cd agents
python devui_app.py
```

O navegador abre em **http://localhost:8080**. Se não abrir, acesse manualmente. O seletor no topo
da tela lista as entidades em dois grupos, e cada grupo funciona de um jeito:

| Grupo no seletor | Entidade | Equivale a | Como enviar |
|---|---|---|---|
| **Agents** | `HelloAgent` | 01 | chat |
| | `AtendenteCadastro` | 02 | chat |
| **Workflows** | `atualizacao_cadastral` | 03 ✏️ | formulário **Configure & Run** |
| | `relatorio_regional` | 04 | formulário **Configure & Run** |
| | `atendimento_handoff` | 05 ✏️ | formulário **Configure & Run** |
| | `analise_concorrente` | 06 | formulário **Configure & Run** |

### Agentes (01 e 02): chat

1. Escolha o agente no seletor.
2. Digite o prompt na caixa de baixo (`Message HelloAgent...`) e tecle Enter.
3. Continue a conversa normalmente: o agente lembra das mensagens anteriores. **New Conversation** começa outra do zero.
4. As chamadas de tool aparecem na conversa e na aba **Tools** do painel da direita.

### Workflows (03 a 06): Configure & Run

Workflow não tem caixa de chat. A entrada vai por um formulário:

1. Escolha o workflow no seletor (grupo **Workflows**). Aparece o **grafo** com as etapas (`input-conversation → extrator → analista → redator`, por exemplo).
2. Clique em **Configure & Run**, embaixo, no centro. Abre a janela **Configure Workflow Inputs**, com vários campos.
3. Preencha só dois:
   - **role**: `user`
   - **contents**: o prompt (copie do [`PROMPTS.md`](PROMPTS.md))

   Deixe os outros campos (`author_name`, `message_id` etc.) em branco.
4. Role a janela até o fim e clique em **Run Workflow**.
5. Acompanhe a execução:
   - no **grafo**, a etapa em execução fica roxa e as concluídas ficam verdes;
   - na **Execution Timeline**, ao lado do grafo, cada etapa vira um item. Clique num item para ver a saída daquela etapa; a última traz a resposta final;
   - o painel da direita mostra os **Events** em tempo real, a aba **Traces** e as chamadas de **Tools**.
6. Para rodar de novo:
   - **Run Again** repete com a mesma entrada (atenção com 03 e 05, que gravam no banco);
   - para outro prompt, clique na setinha ao lado de **Run Again** ▸ **Configure Inputs**.

> No `atendimento_handoff` (05), cada execução é um atendimento novo, sem memória da anterior.
> A conversa com várias trocas fica para o `AtendenteCadastro`.

Para encerrar o DevUI, use `Ctrl+C` no terminal.

Opções: porta diferente com `$env:DEVUI_PORT="8090"`; sem abrir o navegador com `$env:DEVUI_OPEN="0"`.

---

## Parte 4 · Entre ensaios / antes da palestra

Os itens marcados com ✏️ alteram o banco. Rodar o 03, o 05 ou o 07 de novo cria endereços repetidos.
Para voltar ao estado original:

```powershell
docker compose down -v
docker compose up -d
```

Checklist do dia:

- [ ] Docker Desktop aberto e `docker compose up -d` rodado
- [ ] `az account show` mostrando a conta do projeto Foundry
- [ ] ambiente ativado (`(maf)` no prompt)
- [ ] `python 01_hello_agent.py` respondeu
- [ ] banco resetado depois do último ensaio

---

## Problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| `ModuleNotFoundError: agent_framework...` | ambiente não ativado | `C:\venvs\maf\Scripts\Activate.ps1` |
| `Error code: 403 ... does not have permissions` | `az login` com a conta errada, ou sem o papel no projeto | `az login` com a conta do projeto; ou peça o papel **Azure AI User** no projeto |
| `DeploymentNotFound` / modelo não encontrado | `FOUNDRY_MODEL` diferente do nome do deployment | confira em Foundry ▸ Models + endpoints |
| `connection refused` na porta 5432 | Postgres não está rodando | abra o Docker Desktop e rode `docker compose up -d` |
| `⚠ observabilidade desligada: ...` | falta `APPLICATIONINSIGHTS_CONNECTION_STRING` | preencha no `.env`; a demo continua sem telemetria |
| Nada aparece no App Insights | ingestão demora | aguarde de 1 a 3 minutos e busque pelo `operation_Id` |
| DevUI: `address already in use` | porta 8080 ocupada | `$env:DEVUI_PORT="8090"` |
| A mesma resposta aparece de novo ao rodar o 03 | o endereço já tinha sido atualizado no ensaio anterior | resete o banco (Parte 4) |
