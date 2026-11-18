"""
Etapa 2 · Agente com tools
Uma função Python comum (ViaCEP) e uma de banco (Postgres) viram tools
só com type hints + docstring. O agente decide quando chamar cada uma.
"""

from agent_framework import Agent

from _common import banner, executar, get_client
from tools import buscar_cliente_por_cpf, consultar_cep, listar_pedidos_cliente


def build_agent(client) -> Agent:
    return Agent(
        client=client,
        name="AtendenteCadastro",
        description="Etapa 2 · agente com tools: ViaCEP + Postgres (somente leitura).",
        instructions=(
            "Você é um atendente de cadastro. Use as ferramentas antes de responder: "
            "consulte o cliente pelo CPF e valide CEPs no ViaCEP. "
            "Nunca invente dados. Responda em português, de forma objetiva."
            "Primeiramente peça o CPF do cliente antes de qualquer outra ação."
        ),
        tools=[consultar_cep, buscar_cliente_por_cpf, listar_pedidos_cliente],
    )


async def main() -> None:
    agent = build_agent(get_client())

    banner("02 · Agente com tools (ViaCEP + Postgres)")

    perguntas = [
        "Qual é o endereço cadastrado do cliente com CPF 123.456.789-01 e ele tem pedidos em aberto?",
        "O CEP 04538-132 existe? De que bairro e cidade é?",
    ]
    for pergunta in perguntas:
        print(f"\n> {pergunta}")
        result = await agent.run(pergunta)
        print(result)


if __name__ == "__main__":
    executar(main)
