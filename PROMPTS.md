# Prompts para testar cada agente

Roteiro de testes para os 6 agentes/workflows do workshop. Funciona no **DevUI**
(`cd agents && python devui_app.py`) ou no terminal (adaptando a mensagem no `main()` de cada exemplo).
No DevUI, os agentes (1 e 2) recebem o prompt pelo chat. Nos workflows (3 a 6), use **Configure & Run**:
`role` = `user` e `contents` = o prompt
(passo a passo em [`PASSO_A_PASSO.md`](PASSO_A_PASSO.md#workflows-03-a-06-configure--run)).

Cada tabela traz o **caminho feliz**, os **casos de borda** e o **resultado esperado** de acordo com a
carga de dados em `sql/02_seed.sql`. Os itens marcados com ✏️ **gravam no banco**. Veja
[Resetar o banco](#resetar-o-banco) para voltar ao estado original antes da palestra.

> O que observar no DevUI: as chamadas de tool (nome, argumentos e retorno), o grafo dos workflows
> (qual executor está ativo) e a aba **Traces**. Com `OBS_TARGET=azure-monitor` ou `foundry`, a mesma
> execução aparece no Application Insights (veja [Conferir no Application Insights](#conferir-no-application-insights)).

---

## Clientes de referência

| CPF | Cliente | Segmento | Endereço principal | Pedidos |
|---|---|---|---|---|
| 123.456.789-01 | Ana Beatriz Moura | varejo | Av. Paulista, 1578, Conj. 12 · Bela Vista · São Paulo/SP · 01310-100 | PED-2026-0001 Notebook R$ 4.899,90 **enviado** (prev. 24/10) · PED-2026-0002 Mouse entregue |
| 234.567.890-12 | Bruno Carvalho Lima | varejo | Av. Brig. Faria Lima, 3477 · Itaim Bibi · São Paulo/SP | PED-2026-0003 Monitor R$ 2.399,00 **pendente** (prev. 30/10) |
| 345.678.901-23 | Carla Fernandes Souza | premium | Av. Rio Branco, 156, Sala 801 · Centro · Rio de Janeiro/RJ | PED-2026-0004 Cadeira R$ 1.899,00 **pago** (prev. 28/10) · PED-2026-0005 entregue |
| 456.789.012-34 | Diego Martins Rocha | varejo | Praia de Botafogo, 300 · Botafogo · Rio de Janeiro/RJ | PED-2026-0006 Teclado R$ 699,00 **cancelado** |
| 567.890.123-45 | Elaine Pereira Castro | premium | Av. Afonso Pena, 1500, Apto 702 · Centro · Belo Horizonte/MG | PED-2026-0007 Headset R$ 899,00 e PED-2026-0008 Webcam R$ 349,00 **enviados** (prev. 23/10) |
| 678.901.234-56 | Fábio Nogueira Alves | corporativo | R. XV de Novembro, 362 · Centro · Curitiba/PR | PED-2026-0009 Servidor R$ 18.900,00 **pago** (prev. 05/11) |
| 789.012.345-67 | Gabriela Santos Reis | varejo | R. dos Andradas, 1001 · Centro Histórico · Porto Alegre/RS | PED-2026-0010 Tablet entregue |
| 890.123.456-78 | Henrique Oliveira Dias | corporativo | R. Chile, 22, Loja 3 · Centro · Salvador/BA | PED-2026-0011 Licença R$ 5.400,00 **pago** (sem previsão) |
| 901.234.567-89 | Isabela Costa Ramos | varejo | R. do Bom Jesus, 125 · Recife/PE | PED-2026-0012 Impressora R$ 1.299,00 **pendente** (prev. 31/10) |
| 012.345.678-90 | João Pedro Azevedo | premium | Praça da Sé, 1 · Sé · São Paulo/SP · 01001-000 | PED-2026-0013 Smartphone R$ 4.299,00 **enviado** (prev. 25/10) · PED-2026-0014 entregue |
| 112.233.445-56 | Karina Lopes Barbosa | varejo | R. dos Pinheiros, 870, Casa 2 · Pinheiros · São Paulo/SP | PED-2026-0015 Smartwatch R$ 1.599,00 **pendente** (prev. 01/11) |
| 223.344.556-67 | Lucas Teixeira Mendes | varejo | R. Barão do Rio Branco, 1200 · Centro · Fortaleza/CE · 60060-300 | PED-2026-0016 Caixa de som entregue |

"Em aberto" para as tools = `pendente`, `pago` ou `enviado`.

**CEPs úteis (conferidos no ViaCEP):** 04538-132 (Av. Brig. Faria Lima · Itaim Bibi · SP) ·
01001-000 (Praça da Sé · Sé · SP) · 30130-010 (Praça Sete de Setembro · Centro · BH) ·
20040-020 (Praça Pio X · Centro · RJ) · **99999-999 e 00000-000 não existem**.

---

## 1. `HelloAgent` — Etapa 1 · sem tools

Mostra o menor agente possível: só instruções ("responda em no máximo 2 frases").

| Prompt | O que testa | Esperado |
|---|---|---|
| `Explique o que é um agente de IA para quem já programa.` | caminho feliz | Resposta em português, em até 2 frases. |
| `Qual a diferença entre um agente e um workflow no Microsoft Agent Framework?` | conhecimento geral | Até 2 frases. |
| `Escreva um tutorial completo de Python com 10 seções e exemplos de código.` | as instruções valem mais que o pedido | Continua curto, em até 2 frases. |
| `Qual é o endereço do cliente de CPF 123.456.789-01?` | **limite de um agente sem tools** | Diz que não tem acesso aos dados, ou **inventa** um endereço. Qualquer dos dois serve de gancho para a Etapa 2. |

## 2. `AtendenteCadastro` — Etapa 2 · tools ViaCEP + Postgres (somente leitura)

Tools: `consultar_cep`, `buscar_cliente_por_cpf`, `listar_pedidos_cliente`.

| Prompt | O que testa | Esperado |
|---|---|---|
| `Qual é o endereço cadastrado do cliente com CPF 123.456.789-01 e ele tem pedidos em aberto?` | duas tools de banco | Av. Paulista, 1578, Conj. 12, Bela Vista, SP. 1 pedido em aberto: PED-2026-0001 Notebook, **enviado**, previsão 24/10/2026. |
| `O CEP 04538-132 existe? De que bairro e cidade é?` | tool HTTP (ViaCEP) | Sim: Av. Brig. Faria Lima · Itaim Bibi · São Paulo/SP. |
| `O CEP 99999-999 existe?` | CEP inexistente | Tool retorna `{"erro": "CEP 99999999 não encontrado"}`; o agente responde que não existe. |
| `O CEP 1234-56 é válido?` | validação de formato **na tool** | Tool recusa sem chamar a API ("Esperado 8 dígitos"). |
| `Busque o cliente de CPF 999.888.777-66.` | CPF inexistente | "Cliente não encontrado". Não pode inventar dados. |
| `A Carla, CPF 345.678.901-23, tem pedidos em aberto? Quando chegam?` | pedido pago | PED-2026-0004 Cadeira ergonômica, **pago**, previsão 28/10/2026. |
| `O cliente 012.345.678-90 mora em que bairro? Confirme o CEP dele no ViaCEP.` | encadear banco + ViaCEP | Praça da Sé, 1 · Sé · São Paulo/SP · 01001-000 (confirmado). |
| `Qual o endereço do cliente de CPF 345.678.901-23? Confira o CEP no ViaCEP.` | **o agente pegando um dado inconsistente** | No banco: Av. Rio Branco, 156. No ViaCEP, o CEP 20040-020 é da **Praça Pio X**. O agente aponta a divergência (inconsistência real da carga de dados). |
| Na mesma conversa, depois do anterior: `E ela tem pedidos em aberto?` | memória da conversa | Entende que "ela" é a Carla: PED-2026-0004, pago, previsão 28/10/2026. |
| `Atualize o endereço da Ana (CPF 123.456.789-01) para o CEP 01001-000, número 10.` | **menor privilégio** | O agente **não tem** tool de escrita: deve dizer que não consegue atualizar. |

## 3. `atualizacao_cadastral` — Etapa 5 · Sequencial ✏️

`validador_endereco` (ViaCEP) → `analista_cadastro` (Postgres R/W) → `comunicador` (resposta + log).
A ordem importa: não se grava endereço sem validar o CEP.

| Prompt | O que testa | Esperado |
|---|---|---|
| ✏️ `Sou a Ana Beatriz Moura, CPF 123.456.789-01. Mudei de endereço: agora moro no CEP 04538-132, número 3477, torre B, apto 1201. Podem atualizar meu cadastro?` | caminho feliz (cenário da demo) | Novo endereço: Av. Brig. Faria Lima, 3477, Itaim Bibi, SP. **Alerta**: PED-2026-0001 já foi enviado e segue para o endereço antigo. Gera uma linha em `log_agentes` (`resumo_enviado`). |
| ✏️ `Sou a Elaine Pereira Castro, CPF 567.890.123-45. Novo endereço: CEP 20040-020, número 10, sala 5.` | vários pedidos afetados | Praça Pio X, 10, Centro, Rio de Janeiro/RJ. Alerta sobre **2** pedidos enviados (PED-2026-0007 e 0008). |
| `Sou o Bruno Carvalho Lima, CPF 234.567.890-12. Meu novo CEP é 99999-999, número 10.` | **CEP inválido interrompe o fluxo** | O validador diz que o CEP não existe; o analista **não altera nada** e explica o motivo. |
| `Sou a Maria Silva, CPF 999.888.777-66. Novo endereço: CEP 01310-100, número 200.` | cliente inexistente | CEP validado, mas o cliente não é encontrado e nada é gravado. |
| `CPF 112.233.445-56. Mudei para o CEP 05407-002.` | dado faltando (sem número) | Exploratório: veja se o pipeline pede o número ou grava sem ele. Bom gancho para validação de entrada. |

Para conferir a gravação, veja [Conferir o banco](#conferir-o-banco).

## 4. `relatorio_regional` — Etapa 5 · Sequencial analítico (somente leitura)

`extrator` (tool `relatorio_pedidos_por_uf`) → `analista` → `redator`.
No terminal, o exemplo 04 ainda mostra o **workflow-as-agent** (`workflow.as_agent(...)`).

| Prompt | O que testa | Esperado |
|---|---|---|
| `Gere o relatório de pedidos por UF considerando todos os status.` | caminho feliz | PR lidera em valor (R$ 18.900,00 em 1 pedido, maior ticket) · SP lidera em volume (6 pedidos, R$ 13.485,80) · depois BA 5.400 · RS 3.299 · RJ 2.847,90 (3 pedidos) · PE 1.299 · MG 1.248 · CE 459. |
| `Relatório por UF só dos pedidos pendentes.` | filtro de status | SP: 2 pedidos, R$ 3.998,00 · PE: 1 pedido, R$ 1.299,00. |
| `Relatório por UF só dos pedidos enviados.` | outro filtro | SP: 2 pedidos, R$ 9.198,90 · MG: 2 pedidos, R$ 1.248,00. |
| `Relatório dos pedidos pagos, com destaque para amostra pequena.` | análise de amostra pequena | PR 18.900, BA 5.400, RJ 1.899, cada UF com **1 pedido**; o analista deve apontar a amostra pequena. |
| `Relatório dos pedidos com status devolvido.` | status que não existe | A tool devolve lista vazia; o relatório deve dizer que não há dados, **sem inventar números**. |

## 5. `atendimento_handoff` — Etapa 5 · Handoff (triagem → especialista)

`triagem` decide quem atende: `cadastro` (ViaCEP + Postgres R/W) ou `pedidos` (Postgres R).
Está em modo autônomo: o especialista pode fazer mais de um turno, então a resposta pode vir em partes.

| Prompt | O que testa | Esperado |
|---|---|---|
| `Oi, meu CPF é 567.890.123-45. Meus dois pedidos já saíram para entrega? Quando chegam?` | rota **pedidos** | `handoff_to_pedidos`: PED-2026-0007 e 0008 **enviados**, previsão 23/10/2026. |
| ✏️ `Mudei para o CEP 01001-000, número 1, CPF 223.344.556-67. Atualiza meu cadastro por favor.` | rota **cadastro** com escrita | `handoff_to_cadastro`: valida o CEP (Praça da Sé · Sé · SP) e atualiza o endereço do Lucas. |
| `Sou o CPF 123.456.789-01 e quero cancelar o pedido PED-2026-0001.` | especialista sem permissão | Vai para `pedidos`, que lista o pedido mas **não altera** (não há tool de cancelamento). |
| `CPF 901.234.567-89. Mudei para o CEP 00000-000, número 50.` | CEP inválido na rota cadastro | `cadastro` valida, o CEP não existe e **nada é gravado**. |
| `Vocês vendem seguro para notebook?` | fora do escopo | A triagem responde que só atende **cadastro e pedidos**, sem handoff. |
| `CPF 345.678.901-23: quero saber da minha cadeira e também mudar meu endereço para o CEP 30130-010, número 200.` | dois assuntos na mesma mensagem | Exploratório: veja para quem a triagem transfere primeiro e se o segundo assunto é atendido. |

> Cada envio no DevUI é um atendimento novo. O `devui_app.py` cria uma instância nova do handoff a
> cada execução, porque o workflow guarda a conversa anterior. No terminal, o exemplo 05 faz o mesmo.

## 6. `analise_concorrente` — Etapa 5 · Concorrente (somente leitura)

`risco_entrega`, `risco_cadastro` e `oportunidade` rodam **em paralelo** sobre o mesmo cliente,
e a saída é consolidada. No DevUI, cada agente é um item separado na Execution Timeline.

| Prompt | O que testa | Esperado |
|---|---|---|
| `Analise o cliente de CPF 012.345.678-90.` | caminho feliz (cenário da demo) | Entrega: PED-2026-0013 enviado, previsão 25/10. Oportunidade: cliente premium com compra recente de smartphone. |
| `Analise o cliente de CPF 567.890.123-45.` | dois pedidos enviados | Risco de entrega nos 2 pedidos (previsão 23/10). Premium, com oportunidade de acessórios ou serviços. |
| `Analise o cliente de CPF 456.789.012-34.` | cliente sem pedido em aberto | Sem risco de entrega; oportunidade de **reativação** (único pedido cancelado). |
| `Analise o cliente de CPF 678.901.234-56.` | pedido alto ainda não enviado | O pedido de R$ 18.900 está **pago**, não enviado; pelas instruções, risco de entrega olha só `enviado`. Segmento corporativo. |
| `Analise o cliente de CPF 890.123.456-78.` | pedido sem previsão | PED-2026-0011 **pago e sem previsão de entrega**: veja como cada agente lida com o dado ausente. |

> ⚠️ **`risco_cadastro` sempre aponta telefone, complemento e origem como ausentes**, para qualquer
> cliente. O motivo é que `buscar_cliente_por_cpf` lê a view `vw_cliente_resumo`, que não traz esses
> campos. O agente só enxerga o que a tool devolve. É um bom exemplo para a palestra: o desenho da
> tool define o que o agente consegue avaliar. Para corrigir, inclua os campos na view.
>
> 💡 **Ponto para discutir:** os agentes não recebem a data de hoje. Uma previsão de 23/10 só é
> "vencida" se o modelo souber a data atual. Isso mostra por que vale passar contexto (data,
> usuário, canal) nas instruções ou por uma tool.

---

## Conferir o banco

```bash
# endereços da Ana (o novo fica com principal = true e origem = 'agente')
docker compose exec postgres psql -U maf -d workshop -c "SELECT e.id, e.cep, e.logradouro, e.numero, e.principal, e.origem, e.criado_em FROM workshop.enderecos e JOIN workshop.clientes c ON c.id = e.cliente_id WHERE c.cpf = '12345678901' ORDER BY e.id;"

# trilha de auditoria gravada pelas tools
docker compose exec postgres psql -U maf -d workshop -c "SELECT id, agente, acao, cliente_id, criado_em FROM workshop.log_agentes ORDER BY id DESC LIMIT 10;"
```

## Resetar o banco

Depois de testar os itens ✏️, volte ao estado original (apaga o volume e recarrega `sql/`):

```bash
docker compose down -v
docker compose up -d
```

## Conferir no Application Insights

Os exemplos de terminal imprimem o `operation_Id` no final. No DevUI, use o tempo da execução. Em
**Application Insights ▸ Logs**:

```kusto
dependencies
| where timestamp > ago(30m)
| where name startswith "invoke_agent" or name startswith "execute_tool" or name startswith "chat" or name startswith "invoke_workflow"
| project timestamp, name, duracao_ms = round(duration, 0), success, operation_Id
| order by timestamp desc
```

Para ver os prompts, as respostas e os tokens de uma chamada ao modelo, abra o item `chat …` e confira os atributos
`gen_ai.input.messages`, `gen_ai.output.messages` e `gen_ai.usage.*`.
