"""
Etapa 5 (bis) · Orquestração SEQUENCIAL — cenário "Relatório regional"

Mesmo padrão, outro problema: pipeline analítico em vez de transacional.

  [1] extrator   ── Postgres ──▶ agrega pedidos por UF (tool relatorio_pedidos_por_uf)
  [2] analista   ─────────────▶ interpreta: concentração, ticket médio, outliers
  [3] redator    ─────────────▶ escreve um resumo executivo em markdown

Mostra também o "workflow como agente": o pipeline inteiro exposto pela
interface de um agente comum (run / stream), o que permite plugá-lo como
tool de outro agente ou expô-lo via A2A.
"""

from agent_framework.orchestrations import SequentialBuilder

from _common import banner, executar, get_client
from tools import relatorio_pedidos_por_uf


def build_workflow(client):
    extrator = client.as_agent(
        name="extrator",
        instructions=(
            "Você extrai dados. Chame relatorio_pedidos_por_uf com o filtro de status "
            "pedido pelo usuário (ou 'todos') e devolva a tabela EXATAMENTE como veio, "
            "sem interpretar."
        ),
        tools=[relatorio_pedidos_por_uf],
    )
    analista = client.as_agent(
        name="analista",
        instructions=(
            "Você é analista de dados. A partir da tabela anterior, aponte em tópicos: "
            "a UF que concentra mais valor, o maior ticket médio, UFs com apenas 1 pedido "
            "(amostra pequena) e uma hipótese para cada observação. Não invente números."
        ),
    )
    redator = client.as_agent(
        name="redator",
        instructions=(
            "Você escreve para executivos. Transforme a análise anterior em um resumo "
            "markdown com título, 3 bullets de destaque e uma recomendação de 1 frase."
        ),
    )
    return SequentialBuilder(name="relatorio_regional", participants=[extrator, analista, redator]).build()


async def main() -> None:
    workflow = build_workflow(get_client())

    # O workflow inteiro vira um agente: quem chama não sabe que há 3 etapas dentro.
    pipeline = workflow.as_agent(name="RelatorioRegional")

    banner("04 · Sequencial · Relatório regional (Postgres → análise → redação)")

    autor_atual = None
    async for update in pipeline.run("Gere o relatório de pedidos por UF considerando todos os status.", stream=True):
        if update.author_name and update.author_name != autor_atual:
            autor_atual = update.author_name
            print(f"\n\n[{autor_atual}]")
        if update.text:
            print(update.text, end="", flush=True)
    print()


if __name__ == "__main__":
    executar(main)
