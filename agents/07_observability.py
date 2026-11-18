"""
Etapa 6 · Observabilidade

Roda o MESMO workflow sequencial do exemplo 03, agora instrumentado.
Nada muda no agente: a telemetria é OpenTelemetry com as convenções
semânticas GenAI, e o destino é escolhido por variável de ambiente
(veja configurar_observabilidade em _common.py).

  OBS_TARGET=foundry        → Application Insights conectado ao projeto Foundry
                              (Foundry ▸ Agents ▸ Traces / Monitor)
  OBS_TARGET=azure-monitor  → Application Insights via APPLICATIONINSIGHTS_CONNECTION_STRING
                              (Portal ▸ Application Insights ▸ Transaction search / Agents)
  OBS_TARGET=aspire         → Aspire Dashboard local via OTLP (localhost:4317)
                              docker run --rm -it -d -p 18888:18888 -p 4317:18889 \
                                --name aspire mcr.microsoft.com/dotnet/aspire-dashboard:latest
  OBS_TARGET=console        → spans impressos no terminal (debug rápido)
"""

import asyncio
import importlib

from agent_framework import AgentResponse

from _common import banner, configurar_observabilidade, encerrar_observabilidade, get_client

# módulo começa com dígito → importlib
seq = importlib.import_module("03_sequential_atualizacao_cadastral")


async def main() -> None:
    client = get_client()
    destino = await configurar_observabilidade(client)

    banner(f"07 · Observabilidade → {destino}")

    from agent_framework.observability import get_tracer

    tracer = get_tracer()
    workflow = seq.build_workflow(client)

    entrada = (
        "Sou o Lucas Teixeira Mendes, CPF 223.344.556-67. Novo endereço: "
        "CEP 30130-010, número 1500, sala 301. Atualizem, por favor."
    )

    # Um span "pai" por requisição de negócio: no monitor você vê
    # workflow → cada agente → chamada ao modelo → execução de cada tool.
    try:
        with tracer.start_as_current_span("atendimento.atualizacao_cadastral") as span:
            span.set_attribute("workshop.cenario", "atualizacao_cadastral")
            span.set_attribute("workshop.canal", "demo")

            pedacos = []
            async for event in workflow.run(entrada, stream=True):
                if event.type == "executor_invoked":
                    print(f"▶ {event.executor_id}")
                elif event.type == "output":
                    # em streaming, cada pedaço da resposta chega como um evento "output"
                    pedacos.append(event.data)
                elif event.type == "error":
                    print(f"\n✖ erro: {event.data}")
            # from_updates remonta a resposta (juntar os .text na mão duplica o texto final)
            print("\n✔ RESPOSTA FINAL:\n" + seq._texto(AgentResponse.from_updates(pedacos)))

            trace_id = format(span.get_span_context().trace_id, "032x")
    finally:
        # scripts curtos: garante que os spans em lote saiam antes do processo terminar
        encerrar_observabilidade()

    print(f"\nTraces enviados para: {destino}")
    print(f"operation_Id / trace id: {trace_id}")


if __name__ == "__main__":
    asyncio.run(main())
