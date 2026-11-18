"""
Etapa 5 · Orquestração SEQUENCIAL — cenário "Atualização cadastral"

Pipeline de 3 agentes, cada um recebe a conversa acumulada do anterior:

  [1] validador_endereco  ── ViaCEP ──▶ confirma o CEP e completa o endereço
  [2] analista_cadastro   ── Postgres ─▶ localiza o cliente, verifica entregas em
                                        andamento e grava o novo endereço principal
  [3] comunicador         ─────────────▶ redige a resposta final ao cliente/atendente

Por que sequencial? Porque a ordem importa: não se grava endereço sem
validar o CEP, e não se avisa o cliente antes de gravar.
"""

from agent_framework.orchestrations import SequentialBuilder

from _common import banner, executar, get_client
from tools import (
    atualizar_endereco_cliente,
    buscar_cliente_por_cpf,
    consultar_cep,
    listar_pedidos_cliente,
    registrar_log_agente,
)


def build_workflow(client):
    validador = client.as_agent(
        name="validador_endereco",
        instructions=(
            "Você valida endereços. Extraia o CEP e o número informados pelo cliente, "
            "consulte o CEP no ViaCEP com a ferramenta consultar_cep e devolva o endereço "
            "completo (cep, logradouro, número, complemento, bairro, cidade, uf) em uma lista clara. "
            "Se o CEP não existir, diga isso explicitamente e NÃO invente um endereço."
        ),
        tools=[consultar_cep],
    )

    analista = client.as_agent(
        name="analista_cadastro",
        instructions=(
            "Você é analista de cadastro. Com base no endereço validado na mensagem anterior: "
            "1) busque o cliente pelo CPF com buscar_cliente_por_cpf; "
            "2) liste os pedidos em aberto com listar_pedidos_cliente; "
            "3) se o CEP foi validado, grave o novo endereço principal com atualizar_endereco_cliente; "
            "4) relate em tópicos: cliente encontrado?, endereço anterior, endereço novo, "
            "pedidos em aberto que podem ser afetados (código, status, previsão). "
            "Se o CEP não foi validado, NÃO altere nada e explique o motivo."
        ),
        tools=[buscar_cliente_por_cpf, listar_pedidos_cliente, atualizar_endereco_cliente],
    )

    comunicador = client.as_agent(
        name="comunicador",
        instructions=(
            "Você escreve a resposta final para o atendente enviar ao cliente. "
            "Tom cordial e direto, em português. Confirme o endereço atualizado, "
            "alerte sobre pedidos já enviados (que seguirão para o endereço antigo) "
            "e registre um resumo da interação com registrar_log_agente "
            "(agente='comunicador', acao='resumo_enviado')."
        ),
        tools=[registrar_log_agente],
    )

    return (
        SequentialBuilder(
            name="atualizacao_cadastral",
            participants=[validador, analista, comunicador],
            # mostra o que cada etapa produziu, não só a última
            intermediate_output_from=[validador, analista],
        ).build()
    )


async def main() -> None:
    workflow = build_workflow(get_client())

    pedido_cliente = (
        "Sou a Ana Beatriz Moura, CPF 123.456.789-01. Mudei de endereço: "
        "agora moro no CEP 04538-132, número 3477, torre B, apto 1201. "
        "Podem atualizar meu cadastro?"
    )

    banner("03 · Sequencial · Atualização cadastral (ViaCEP → Postgres → resposta)")
    print(f"\n> {pedido_cliente}\n")

    async for event in workflow.run(pedido_cliente, stream=True):
        if event.type == "executor_invoked":
            print(f"\n▶ iniciando {event.executor_id}")
        elif event.type == "intermediate":
            print(f"\n[{event.executor_id}] saída intermediária:\n{_texto(event.data)}")
        elif event.type == "output":
            print(f"\n✔ RESPOSTA FINAL:\n{_texto(event.data)}")
        elif event.type == "error":
            print(f"\n✖ erro: {event.data}")


def _texto(data) -> str:
    """AgentResponse → texto da última mensagem; qualquer outra coisa → str()."""
    messages = getattr(data, "messages", None)
    if messages:
        return messages[-1].text or ""
    return str(data)


if __name__ == "__main__":
    executar(main)
