"""
Tool de consulta de CEP via ViaCEP (https://viacep.com.br).

No Microsoft Agent Framework, uma tool é só uma função Python com
type hints e docstring. O framework gera o JSON schema a partir das
anotações `Annotated[tipo, "descrição"]` e a docstring vira a
descrição da ferramenta para o modelo.
"""

from __future__ import annotations

import json
import re
from typing import Annotated

import httpx

VIACEP_URL = "https://viacep.com.br/ws/{cep}/json/"


def _normalizar_cep(cep: str) -> str:
    """Mantém apenas dígitos e valida o tamanho."""
    digitos = re.sub(r"\D", "", cep or "")
    if len(digitos) != 8:
        raise ValueError(f"CEP inválido: '{cep}'. Esperado 8 dígitos.")
    return digitos


async def consultar_cep(
    cep: Annotated[str, "CEP brasileiro com 8 dígitos, com ou sem hífen. Ex.: 01310-100"],
) -> str:
    """Consulta um CEP na API pública ViaCEP e retorna o endereço completo
    (logradouro, bairro, cidade, UF, DDD) em JSON. Use antes de cadastrar
    ou atualizar qualquer endereço para garantir que o CEP existe e para
    preencher os campos automaticamente."""
    try:
        digitos = _normalizar_cep(cep)
    except ValueError as exc:
        return json.dumps({"erro": str(exc)}, ensure_ascii=False)

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(VIACEP_URL.format(cep=digitos))

    if resp.status_code != 200:
        return json.dumps({"erro": f"ViaCEP respondeu HTTP {resp.status_code}"}, ensure_ascii=False)

    dados = resp.json()
    if dados.get("erro"):
        return json.dumps({"erro": f"CEP {digitos} não encontrado"}, ensure_ascii=False)

    endereco = {
        "cep": digitos,
        "logradouro": dados.get("logradouro", ""),
        "complemento": dados.get("complemento", ""),
        "bairro": dados.get("bairro", ""),
        "cidade": dados.get("localidade", ""),
        "uf": dados.get("uf", ""),
        "ddd": dados.get("ddd", ""),
        "fonte": "viacep",
    }
    return json.dumps(endereco, ensure_ascii=False)


if __name__ == "__main__":  # teste rápido: python -m tools.viacep
    import asyncio

    print(asyncio.run(consultar_cep("01310-100")))
