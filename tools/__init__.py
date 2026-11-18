"""Tools reutilizáveis pelos agentes do workshop."""

from .viacep import consultar_cep
from .postgres import (
    buscar_cliente_por_cpf,
    listar_pedidos_cliente,
    atualizar_endereco_cliente,
    relatorio_pedidos_por_uf,
    registrar_log_agente,
)

__all__ = [
    "consultar_cep",
    "buscar_cliente_por_cpf",
    "listar_pedidos_cliente",
    "atualizar_endereco_cliente",
    "relatorio_pedidos_por_uf",
    "registrar_log_agente",
]
