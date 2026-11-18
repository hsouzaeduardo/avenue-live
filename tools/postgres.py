"""
Tools de acesso ao PostgreSQL (schema `workshop`).

Princípios usados aqui, que valem a pena comentar na apresentação:
  • Cada tool faz UMA coisa e retorna JSON serializado — o modelo lê
    texto, então devolvemos texto estruturado e previsível.
  • Nada de SQL livre vindo do LLM: as queries são fixas e parametrizadas.
    A autonomia do agente fica em "qual tool chamar", não em "qual SQL rodar".
  • Toda escrita (UPDATE/INSERT) gera uma linha em `log_agentes` — trilha
    de auditoria barata que depois aparece lado a lado com os traces.
"""

from __future__ import annotations

import json
import os
import re
from decimal import Decimal
from datetime import date, datetime
from typing import Annotated, Any

import psycopg
from psycopg.rows import dict_row


# ---------------------------------------------------------------------
# Infraestrutura
# ---------------------------------------------------------------------
def _database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL não definida (veja .env.example)")
    return url


async def _conn() -> psycopg.AsyncConnection:
    conn = await psycopg.AsyncConnection.connect(_database_url(), row_factory=dict_row)
    await conn.execute("SET search_path TO workshop, public")
    return conn


def _json(obj: Any) -> str:
    def default(o: Any):
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        return str(o)

    return json.dumps(obj, ensure_ascii=False, default=default)


def _so_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


# ---------------------------------------------------------------------
# Tools de LEITURA
# ---------------------------------------------------------------------
async def buscar_cliente_por_cpf(
    cpf: Annotated[str, "CPF do cliente, com ou sem pontuação (11 dígitos)"],
) -> str:
    """Busca um cliente pelo CPF e retorna seus dados cadastrais, o endereço
    principal atual e um resumo de pedidos em aberto. Retorna {"erro": ...}
    se o CPF não existir na base."""
    cpf_digitos = _so_digitos(cpf)
    async with await _conn() as conn:
        row = await (
            await conn.execute("SELECT * FROM vw_cliente_resumo WHERE cpf = %s", (cpf_digitos,))
        ).fetchone()
    if not row:
        return _json({"erro": f"Cliente com CPF {cpf_digitos} não encontrado"})
    return _json(row)


async def listar_pedidos_cliente(
    cpf: Annotated[str, "CPF do cliente (11 dígitos)"],
    apenas_abertos: Annotated[bool, "Se true, retorna só pedidos pendentes, pagos ou enviados"] = True,
) -> str:
    """Lista os pedidos de um cliente (código, descrição, valor, status e
    previsão de entrega). Útil para verificar se há entregas em andamento
    antes de alterar o endereço."""
    cpf_digitos = _so_digitos(cpf)
    sql = """
        SELECT p.codigo, p.descricao, p.valor, p.status, p.criado_em, p.previsao_entrega
        FROM pedidos p
        JOIN clientes c ON c.id = p.cliente_id
        WHERE c.cpf = %s
          AND (%s = FALSE OR p.status IN ('pendente','pago','enviado'))
        ORDER BY p.criado_em DESC
    """
    async with await _conn() as conn:
        rows = await (await conn.execute(sql, (cpf_digitos, apenas_abertos))).fetchall()
    return _json({"cpf": cpf_digitos, "total": len(rows), "pedidos": rows})


async def relatorio_pedidos_por_uf(
    status: Annotated[str, "Filtro de status: pendente, pago, enviado, entregue, cancelado ou 'todos'"] = "todos",
) -> str:
    """Agrega os pedidos por UF do endereço principal do cliente: quantidade,
    valor total e ticket médio. Base para análises regionais."""
    status = (status or "todos").lower()
    sql = """
        SELECT e.uf,
               COUNT(p.id)            AS qtd_pedidos,
               SUM(p.valor)           AS valor_total,
               ROUND(AVG(p.valor), 2) AS ticket_medio
        FROM pedidos p
        JOIN clientes  c ON c.id = p.cliente_id
        JOIN enderecos e ON e.cliente_id = c.id AND e.principal
        WHERE (%s = 'todos' OR p.status::text = %s)
        GROUP BY e.uf
        ORDER BY valor_total DESC
    """
    async with await _conn() as conn:
        rows = await (await conn.execute(sql, (status, status))).fetchall()
    return _json({"filtro_status": status, "linhas": rows})


# ---------------------------------------------------------------------
# Tools de ESCRITA
# ---------------------------------------------------------------------
async def atualizar_endereco_cliente(
    cpf: Annotated[str, "CPF do cliente (11 dígitos)"],
    cep: Annotated[str, "CEP já validado no ViaCEP (8 dígitos)"],
    logradouro: Annotated[str, "Logradouro retornado pelo ViaCEP"],
    numero: Annotated[str, "Número informado pelo cliente"],
    bairro: Annotated[str, "Bairro retornado pelo ViaCEP"],
    cidade: Annotated[str, "Cidade retornada pelo ViaCEP"],
    uf: Annotated[str, "UF com 2 letras"],
    complemento: Annotated[str, "Complemento (apto, bloco, sala). Vazio se não houver"] = "",
) -> str:
    """Define um NOVO endereço principal para o cliente. O endereço anterior é
    mantido no histórico (principal = false). Só chame depois de validar o CEP
    com consultar_cep. Registra a ação em log_agentes."""
    cpf_digitos = _so_digitos(cpf)
    cep_digitos = _so_digitos(cep)
    if len(cep_digitos) != 8:
        return _json({"erro": "CEP deve ter 8 dígitos"})

    async with await _conn() as conn:
        async with conn.transaction():
            cliente = await (
                await conn.execute("SELECT id, nome FROM clientes WHERE cpf = %s", (cpf_digitos,))
            ).fetchone()
            if not cliente:
                return _json({"erro": f"Cliente com CPF {cpf_digitos} não encontrado"})

            await conn.execute(
                "UPDATE enderecos SET principal = FALSE WHERE cliente_id = %s AND principal",
                (cliente["id"],),
            )
            novo = await (
                await conn.execute(
                    """
                    INSERT INTO enderecos
                        (cliente_id, cep, logradouro, numero, complemento, bairro, cidade, uf, principal, origem)
                    VALUES (%s, %s, %s, %s, NULLIF(%s, ''), %s, %s, %s, TRUE, 'agente')
                    RETURNING id, cep, logradouro, numero, complemento, bairro, cidade, uf
                    """,
                    (cliente["id"], cep_digitos, logradouro, numero, complemento, bairro, cidade, uf.upper()),
                )
            ).fetchone()

            await conn.execute(
                "INSERT INTO log_agentes (agente, acao, cliente_id, detalhes) VALUES (%s, %s, %s, %s)",
                ("analista_cadastro", "atualizar_endereco", cliente["id"], _json(novo)),
            )

    return _json({"ok": True, "cliente": cliente["nome"], "endereco_principal": novo})


async def registrar_log_agente(
    agente: Annotated[str, "Nome do agente que executou a ação"],
    acao: Annotated[str, "Ação executada, em snake_case (ex.: resumo_enviado)"],
    detalhes: Annotated[str, "Texto livre ou JSON com o contexto da ação"],
    cpf: Annotated[str, "CPF do cliente relacionado, se houver"] = "",
) -> str:
    """Grava uma entrada na trilha de auditoria (tabela log_agentes). Use para
    registrar decisões relevantes do agente que não alteram outras tabelas."""
    cpf_digitos = _so_digitos(cpf)
    async with await _conn() as conn:
        cliente_id = None
        if cpf_digitos:
            row = await (await conn.execute("SELECT id FROM clientes WHERE cpf = %s", (cpf_digitos,))).fetchone()
            cliente_id = row["id"] if row else None
        try:
            detalhes_json = json.loads(detalhes)
        except (TypeError, ValueError):
            detalhes_json = {"texto": detalhes}
        await conn.execute(
            "INSERT INTO log_agentes (agente, acao, cliente_id, detalhes) VALUES (%s, %s, %s, %s)",
            (agente, acao, cliente_id, _json(detalhes_json)),
        )
        await conn.commit()
    return _json({"ok": True})
