"""
Etapa 5 (quater) · Orquestração CONCORRENTE — cenário "Segunda opinião"

Três agentes recebem a MESMA entrada ao mesmo tempo e um agregador
consolida. Útil quando as tarefas são independentes e você quer cortar
latência ou obter perspectivas diferentes sobre o mesmo dado.

              ┌─▶ risco_entrega ──┐
  entrada ────┼─▶ risco_cadastro ─┼──▶ agregador ──▶ saída
              └─▶ oportunidade ───┘
"""

from agent_framework.orchestrations import ConcurrentBuilder

from _common import banner, executar, get_client
from tools import buscar_cliente_por_cpf, listar_pedidos_cliente


def build_workflow(client):
    risco_entrega = client.as_agent(
        name="risco_entrega",
        instructions=(
            "Avalie risco de ENTREGA: pedidos 'enviado' com previsão próxima ou vencida. "
            "Use listar_pedidos_cliente. Responda em 2 bullets no máximo."
        ),
        tools=[listar_pedidos_cliente],
    )
    risco_cadastro = client.as_agent(
        name="risco_cadastro",
        instructions=(
            "Avalie risco CADASTRAL: dados ausentes (bairro, complemento, telefone) ou "
            "endereço sem origem validada. Use buscar_cliente_por_cpf. 2 bullets no máximo."
        ),
        tools=[buscar_cliente_por_cpf],
    )
    oportunidade = client.as_agent(
        name="oportunidade",
        instructions=(
            "Identifique OPORTUNIDADE comercial pelo segmento e histórico de pedidos "
            "(buscar_cliente_por_cpf + listar_pedidos_cliente com apenas_abertos=false). "
            "1 sugestão objetiva."
        ),
        tools=[buscar_cliente_por_cpf, listar_pedidos_cliente],
    )

    return ConcurrentBuilder(
        name="analise_concorrente",
        participants=[risco_entrega, risco_cadastro, oportunidade],
        intermediate_output_from=[risco_entrega, risco_cadastro, oportunidade],
    ).build()


async def main() -> None:
    workflow = build_workflow(get_client())
    banner("06 · Concorrente · Três análises em paralelo sobre o mesmo cliente")

    async for event in workflow.run("Analise o cliente de CPF 012.345.678-90.", stream=True):
        if event.type == "intermediate":
            print(f"\n[{event.executor_id}]\n{_texto(event.data)}")
        elif event.type == "output":
            print(f"\n✔ CONSOLIDADO:\n{_texto(event.data)}")


def _texto(data) -> str:
    messages = getattr(data, "messages", None)
    if messages:
        return "\n".join(m.text for m in messages if m.text)
    if isinstance(data, list):
        return "\n".join(getattr(m, "text", str(m)) for m in data)
    return str(data)


if __name__ == "__main__":
    executar(main)
