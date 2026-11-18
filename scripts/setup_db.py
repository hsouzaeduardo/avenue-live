"""
Cria o esquema e carrega os dados de demonstração em um PostgreSQL
já existente (alternativa ao docker-compose, para quem tem um
Postgres local, Azure Database for PostgreSQL etc.).

Uso:
    python scripts/setup_db.py            # usa DATABASE_URL do .env
    python scripts/setup_db.py --reset    # dropa o schema antes

DATABASE_URL no formato:
    postgresql://usuario:senha@host:5432/workshop
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql"


def main() -> int:
    load_dotenv(ROOT / ".env")

    parser = argparse.ArgumentParser(description="Cria e popula o banco do workshop.")
    parser.add_argument("--reset", action="store_true", help="dropa o schema 'workshop' antes de recriar")
    args = parser.parse_args()

    url = os.getenv("DATABASE_URL")
    if not url:
        print("DATABASE_URL não definida. Veja .env.example.", file=sys.stderr)
        return 1

    scripts = sorted(SQL_DIR.glob("*.sql"))
    if not scripts:
        print(f"Nenhum .sql encontrado em {SQL_DIR}", file=sys.stderr)
        return 1

    with psycopg.connect(url, autocommit=True) as conn:
        if args.reset:
            print("• Removendo schema 'workshop'…")
            conn.execute("DROP SCHEMA IF EXISTS workshop CASCADE")

        for script in scripts:
            print(f"• Executando {script.name}…")
            conn.execute(script.read_text(encoding="utf-8"))

        with conn.cursor() as cur:
            cur.execute("SET search_path TO workshop")
            cur.execute(
                """
                SELECT 'clientes', COUNT(*) FROM clientes
                UNION ALL SELECT 'enderecos', COUNT(*) FROM enderecos
                UNION ALL SELECT 'pedidos', COUNT(*) FROM pedidos
                """
            )
            for tabela, total in cur.fetchall():
                print(f"  {tabela:<10} {total:>4} linhas")

    print("✔ Banco pronto.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
