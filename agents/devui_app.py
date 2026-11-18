"""
DevUI · todos os agentes e workflows do workshop numa interface web

    cd agents
    python devui_app.py           # abre http://localhost:8080  (porta: DEVUI_PORT)

Cada entidade é construída pelas MESMAS funções dos exemplos (build_agent /
build_workflow): o DevUI é só mais uma "porta de entrada"; o agente não muda.
Prompts sugeridos para cada um: ../PROMPTS.md

Observabilidade
  • aba Traces do DevUI: sempre ligada (spans de cada execução na própria interface)
  • OBS_TARGET=azure-monitor | foundry | aspire: os mesmos spans também vão para lá
"""

import asyncio
import importlib
import os
import sys

from agent_framework.devui import serve

from _common import configurar_observabilidade, get_client

PORTA = int(os.getenv("DEVUI_PORT", "8080"))


def construir_entidades() -> tuple[list, dict]:
    """Retorna as entidades e, para as que guardam estado entre execuções, a função que
    cria uma instância nova (usada por recriar_a_cada_execucao)."""
    client = get_client()
    exemplo = importlib.import_module  # módulos começam com dígito → importlib
    handoff = exemplo("05_handoff_atendimento")

    atendimento = handoff.build_workflow(client)
    entidades = [
        exemplo("01_hello_agent").build_agent(client),
        exemplo("02_agent_tools").build_agent(client),
        exemplo("03_sequential_atualizacao_cadastral").build_workflow(client),
        exemplo("04_sequential_relatorio_regional").build_workflow(client),
        atendimento,
        exemplo("06_concurrent_analise").build_workflow(client),
    ]
    return entidades, {id(atendimento): lambda: handoff.build_workflow(client)}


def ligar_observabilidade() -> str:
    alvo = os.getenv("OBS_TARGET", "console").lower()
    if alvo not in ("console", "none"):
        try:
            return asyncio.run(configurar_observabilidade())
        except Exception as exc:  # noqa: BLE001 — observabilidade nunca derruba a demo
            print(f"⚠ observabilidade remota desligada: {exc}")

    # Sem destino remoto: provider OpenTelemetry local, só para alimentar a aba Traces do DevUI.
    from agent_framework.observability import configure_otel_providers

    os.environ["ENABLE_CONSOLE_EXPORTERS"] = "false"
    configure_otel_providers(enable_sensitive_data=True)
    return "somente a aba Traces do DevUI"


def usar_selector_loop_no_uvicorn() -> None:
    """No Windows o uvicorn cria um ProactorEventLoop (ignora a policy definida em
    _common.py), e o psycopg async das tools de banco não funciona nele."""
    if sys.platform != "win32":
        return
    import uvicorn

    run_original = uvicorn.run

    def run(app, **kwargs):
        kwargs.setdefault("loop", "asyncio:SelectorEventLoop")
        return run_original(app, **kwargs)

    uvicorn.run = run


def evitar_texto_duplicado_no_devui() -> None:
    """Contorno para o DevUI (beta): o client da Responses API encerra cada mensagem com um
    update contendo o texto COMPLETO e merge_mode="replace". O DevUI trata esse update como
    mais um delta, e a resposta aparece duas vezes na tela. Como os deltas já trouxeram o
    mesmo texto, descartamos só esse update de "replace" antes de mapear para a interface."""
    import copy

    from agent_framework_devui._mapper import MessageMapper

    converter_original = MessageMapper._convert_agent_update

    def _eh_replace(content) -> bool:
        return content.type == "text" and getattr(content, "merge_mode", None) == "replace"

    async def converter(self, update, context):
        contents = getattr(update, "contents", None)
        if contents and any(_eh_replace(c) for c in contents):
            update = copy.copy(update)
            update.contents = [c for c in contents if not _eh_replace(c)]
        return await converter_original(self, update, context)

    MessageMapper._convert_agent_update = converter


def recriar_a_cada_execucao(fabricas: dict) -> None:
    """O workflow de handoff guarda a conversa da execução anterior, e o DevUI reaproveita a
    mesma instância (cache) a cada "Run". Com isso, a 2ª execução herda o estado da 1ª e falha
    ("Messages are required for chat completions"). Para essas entidades, entregamos uma
    instância nova a cada execução, como o exemplo 05 faz no terminal."""
    from agent_framework_devui._discovery import EntityDiscovery

    carregar_original = EntityDiscovery.load_entity
    por_entity_id: dict = {}

    async def load_entity(self, entity_id, checkpoint_manager=None):
        obj = await carregar_original(self, entity_id, checkpoint_manager=checkpoint_manager)
        fabrica = por_entity_id.get(entity_id) or fabricas.pop(id(obj), None)
        if fabrica is None:
            return obj
        por_entity_id[entity_id] = fabrica
        self._loaded_objects[entity_id] = novo = fabrica()
        return novo

    EntityDiscovery.load_entity = load_entity


if __name__ == "__main__":
    destino = ligar_observabilidade()
    entidades, fabricas = construir_entidades()
    usar_selector_loop_no_uvicorn()
    evitar_texto_duplicado_no_devui()
    recriar_a_cada_execucao(fabricas)

    print(f"DevUI → http://localhost:{PORTA}  ·  {len(entidades)} entidades  ·  telemetria: {destino}")
    # auth desligada só porque o servidor escuta em 127.0.0.1 (o DevUI recusa isso em outros hosts)
    serve(entities=entidades, port=PORTA, auto_open=os.getenv("DEVUI_OPEN", "1") != "0", auth_enabled=False)
