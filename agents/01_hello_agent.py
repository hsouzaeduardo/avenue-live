"""
Etapa 1 · Hello Agent
O menor agente possível: cliente + instruções + run().
"""

from agent_framework import Agent

from _common import banner, executar, get_client


def build_agent(client) -> Agent:
    return Agent(
        client=client,
        name="HelloAgent",
        description="Etapa 1 · o menor agente possível: só instruções, sem tools.",
        instructions="Você é um assistente direto. Responda em português, em no máximo 2 frases. e sempre termine com emoji.",
    )


async def main() -> None:
    agent = build_agent(get_client())

    banner("01 · Hello Agent")
    result = await agent.run("Explique o que é um agente de IA para quem já programa.")
    print(result)


if __name__ == "__main__":
    executar(main)
