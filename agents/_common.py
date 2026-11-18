"""
Utilitários compartilhados pelos exemplos.

A ideia central desta função é o argumento de "flexibilidade" da
apresentação: o agente não é acoplado ao modelo. Trocar o provider
é trocar o objeto `client`; instruções, tools e workflows não mudam.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Permite `python agents/03_...py` a partir da raiz do projeto
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

# Windows: o psycopg em modo async não funciona com o ProactorEventLoop (padrão
# do asyncio no Windows). Trocamos para o SelectorEventLoop antes do asyncio.run().
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def get_client():
    """Retorna um chat client conforme MODEL_PROVIDER (foundry | azure-openai | openai).

    - foundry       : modelo implantado em um projeto do Microsoft Foundry (padrão da demo)
    - azure-openai  : recurso Azure OpenAI direto (endpoint + deployment)
    - openai        : API da OpenAI (ou endpoint compatível, ex.: Ollama/vLLM)
    """
    provider = os.getenv("MODEL_PROVIDER", "foundry").lower()

    if provider == "foundry":
        from agent_framework.foundry import FoundryChatClient
        from azure.identity import AzureCliCredential

        return FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["FOUNDRY_MODEL"],
            credential=AzureCliCredential(),
        )

    if provider == "azure-openai":
        from agent_framework.azure import AzureOpenAIChatClient
        from azure.identity import AzureCliCredential

        return AzureOpenAIChatClient(
            endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT"],
            credential=AzureCliCredential(),
        )

    if provider == "openai":
        from agent_framework.openai import OpenAIChatClient

        return OpenAIChatClient(
            model_id=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url=os.environ.get("OPENAI_BASE_URL"),  # ex.: http://localhost:11434/v1 (Ollama)
        )

    raise ValueError(f"MODEL_PROVIDER desconhecido: {provider}")


async def configurar_observabilidade(client=None) -> str:
    """Liga a telemetria (OpenTelemetry + convenções GenAI) conforme OBS_TARGET.

    - console        : spans impressos no terminal (padrão)
    - aspire         : Aspire Dashboard local via OTLP (localhost:4317)
    - azure-monitor  : Application Insights a partir de APPLICATIONINSIGHTS_CONNECTION_STRING
                       (funciona com qualquer MODEL_PROVIDER)
    - foundry        : Application Insights conectado ao projeto Foundry. Usa
                       APPLICATIONINSIGHTS_CONNECTION_STRING se definida; senão busca no projeto.
    - none           : sem telemetria

    enable_sensitive_data=True grava prompts/respostas nos spans: ótimo para demo,
    avalie com cuidado em produção. Retorna uma descrição do destino.
    """
    alvo = os.getenv("OBS_TARGET", "console").lower()

    if alvo == "none":
        return "desligada"

    if alvo in ("azure-monitor", "foundry"):
        from agent_framework.observability import create_resource, enable_instrumentation
        from azure.monitor.opentelemetry import configure_azure_monitor

        conn_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        if not conn_string and alvo == "foundry":
            project_client = getattr(client or get_client(), "project_client", None)
            if project_client is None:
                raise RuntimeError("OBS_TARGET=foundry exige MODEL_PROVIDER=foundry (ou defina APPLICATIONINSIGHTS_CONNECTION_STRING).")
            try:
                conn_string = await project_client.telemetry.get_application_insights_connection_string()
            except Exception as exc:  # noqa: BLE001 — mensagem amigável na demo
                raise RuntimeError(
                    "Não consegui obter o Application Insights do projeto Foundry. Conecte um App Insights em "
                    "Foundry ▸ Operate/Monitor, ou defina APPLICATIONINSIGHTS_CONNECTION_STRING no .env. "
                    f"Detalhe: {exc}"
                ) from exc
        if not conn_string:
            raise RuntimeError("OBS_TARGET=azure-monitor exige APPLICATIONINSIGHTS_CONNECTION_STRING no .env.")

        # A distro liga também o instrumentador do SDK azure-ai-projects, que avisa "GenAI tracing
        # is not enabled". Não precisamos dele: o Agent Framework já emite os spans GenAI
        # (ativá-lo duplicaria as chamadas ao modelo). Só silenciamos o aviso.
        import logging

        logging.getLogger("azure.ai.projects.telemetry").setLevel(logging.ERROR)

        configure_azure_monitor(
            connection_string=conn_string,
            resource=create_resource(service_name=os.getenv("OTEL_SERVICE_NAME", "maf-workshop")),
            # sem `views`: além das métricas gen_ai/agent_framework (tokens, duração), vão também
            # as métricas HTTP (latência do Foundry e do ViaCEP) — tudo no App Insights.
            # Só os logs do framework viram "traces" no App Insights. Capturar o logger raiz
            # inclui os avisos de retry do próprio exporter: se a rede cair, cada falha gera
            # novos logs para enviar e o processo não termina.
            logger_name="agent_framework",
        )
        enable_instrumentation(enable_sensitive_data=True)
        return "Azure Monitor / Application Insights" + (" (projeto Foundry)" if alvo == "foundry" else "")

    from agent_framework.observability import configure_otel_providers

    if alvo == "aspire":
        os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        os.environ.setdefault("OTEL_SERVICE_NAME", "maf-workshop")
        configure_otel_providers(enable_sensitive_data=True)
        return "Aspire Dashboard (http://localhost:18888)"

    if alvo != "console":
        raise ValueError(f"OBS_TARGET desconhecido: {alvo}")

    os.environ.setdefault("ENABLE_CONSOLE_EXPORTERS", "true")
    configure_otel_providers(enable_sensitive_data=True)
    return "console"


def encerrar_observabilidade(timeout_s: float = 15) -> None:
    """Força o envio dos spans/métricas/logs pendentes antes do script terminar.
    Exporters em lote (Azure Monitor, OTLP) podem perder dados de scripts curtos."""
    from opentelemetry import _logs, metrics, trace

    for provider in (trace.get_tracer_provider(), metrics.get_meter_provider(), _logs.get_logger_provider()):
        flush = getattr(provider, "force_flush", None)
        if flush:
            flush(timeout_millis=int(timeout_s * 1000))


def executar(main) -> None:
    """Substitui `asyncio.run(main())` nos exemplos 01–06: liga a telemetria remota
    (OBS_TARGET = azure-monitor | foundry | aspire), agrupa a execução inteira em um
    span com o nome do script (uma operação no App Insights) e envia tudo antes de sair.

    OBS_TARGET=console fica só no 07, para os spans não poluírem a saída das outras demos.
    Se a telemetria não puder ser ligada, a demo segue sem ela (com um aviso).
    """
    nome = Path(sys.argv[0]).stem or "maf-workshop"

    async def _rodar() -> None:
        alvo = os.getenv("OBS_TARGET", "console").lower()
        destino = None
        if alvo not in ("console", "none"):
            try:
                destino = await configurar_observabilidade()
            except Exception as exc:  # noqa: BLE001 — observabilidade nunca derruba a demo
                print(f"⚠ observabilidade desligada: {exc}")

        if not destino:
            await main()
            return

        from agent_framework.observability import get_tracer

        try:
            with get_tracer().start_as_current_span(f"demo.{nome}") as span:
                span.set_attribute("workshop.script", nome)
                await main()
                trace_id = format(span.get_span_context().trace_id, "032x")
        finally:
            encerrar_observabilidade()
        print(f"\n📡 telemetria → {destino} · operation_Id {trace_id}")

    asyncio.run(_rodar())


def banner(titulo: str) -> None:
    print("\n" + "=" * 72)
    print(f" {titulo}")
    print("=" * 72)
