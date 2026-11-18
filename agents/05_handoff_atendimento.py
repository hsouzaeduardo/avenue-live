"""
Etapa 5 (ter) · Orquestração HANDOFF — cenário "Atendimento com triagem"

Aqui a ORDEM NÃO é fixa: o agente de triagem lê a mensagem e passa o bastão
para o especialista certo. Cada especialista tem só as tools do seu domínio.

           ┌──────────┐   handoff   ┌──────────────┐
  usuário ─▶ triagem  ├────────────▶│ cadastro     │  consultar_cep, buscar_cliente, atualizar_endereco
           │          ├────────────▶│ pedidos      │  listar_pedidos, buscar_cliente
           └──────────┘             └──────────────┘

Sequencial = VOCÊ decide a ordem.  Handoff = o LLM decide quem atende.
"""

from agent_framework.orchestrations import HandoffBuilder

from _common import banner, executar, get_client
from tools import (
    atualizar_endereco_cliente,
    buscar_cliente_por_cpf,
    consultar_cep,
    listar_pedidos_cliente,
)


def build_workflow(client):
    triagem = client.as_agent(
        name="triagem",
        # exigido pelo HandoffBuilder: o handoff "curto-circuita" a tool de transferência,
        # e o histórico local precisa ficar igual ao que o serviço viu
        require_per_service_call_history_persistence=True,
        instructions=(
            "Você é a triagem do atendimento. Leia a mensagem e transfira para o "
            "especialista adequado: 'cadastro' para endereço/dados pessoais, "
            "'pedidos' para status/entrega/valores. Não responda ao mérito; apenas encaminhe. "
            "Se a mensagem não for sobre nenhum dos dois, responda educadamente que só "
            "atende cadastro e pedidos."
        ),
    )
    cadastro = client.as_agent(
        name="cadastro",
        require_per_service_call_history_persistence=True,
        instructions=(
            "Especialista em cadastro. Valide CEPs com consultar_cep antes de qualquer "
            "atualização, localize o cliente pelo CPF e só então use atualizar_endereco_cliente. "
            "Encerre com um resumo do que foi feito."
        ),
        tools=[consultar_cep, buscar_cliente_por_cpf, atualizar_endereco_cliente],
    )
    pedidos = client.as_agent(
        name="pedidos",
        require_per_service_call_history_persistence=True,
        instructions=(
            "Especialista em pedidos. Localize o cliente pelo CPF e liste os pedidos com "
            "listar_pedidos_cliente. Responda com código, status e previsão de entrega. "
            "Nunca altere dados."
        ),
        tools=[buscar_cliente_por_cpf, listar_pedidos_cliente],
    )

    return (
        HandoffBuilder(
            name="atendimento_handoff",
            participants=[triagem, cadastro, pedidos],
        )
        .with_start_agent(triagem)
        # modo autônomo: os agentes seguem sem esperar nova entrada humana
        # (ideal para demo; em produção, use turn_limits ou request_info)
        .with_autonomous_mode(turn_limits={"triagem": 2, "cadastro": 4, "pedidos": 3})
        .build()
    )


async def main() -> None:
    client = get_client()
    banner("05 · Handoff · Atendimento com triagem")

    mensagens = [
        "Oi, meu CPF é 567.890.123-45. Meus dois pedidos já saíram para entrega? Quando chegam?",
        "Mudei para o CEP 01001-000, número 1, CPF 223.344.556-67. Atualiza meu cadastro por favor.",
    ]

    for msg in mensagens:
        print(f"\n> {msg}")
        # um workflow novo por atendimento: o handoff guarda a conversa, e reaproveitar a
        # instância faria a 2ª mensagem continuar o atendimento da 1ª
        workflow = build_workflow(client)
        async for event in workflow.run(msg, stream=True):
            if event.type == "executor_invoked":
                print(f"  ▶ {event.executor_id}")
            elif event.type == "output":
                print(f"\n✔ {_texto(event.data)}")
            elif event.type == "error":
                print(f"\n✖ erro: {event.data}")


def _texto(data) -> str:
    messages = getattr(data, "messages", None)
    if messages:
        return "\n".join(f"[{m.author_name or 'assistant'}] {m.text}" for m in messages if m.text)
    if isinstance(data, list):
        return "\n".join(f"[{getattr(m, 'author_name', 'assistant')}] {getattr(m, 'text', m)}" for m in data)
    return str(data)


if __name__ == "__main__":
    executar(main)
