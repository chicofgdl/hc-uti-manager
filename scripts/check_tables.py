import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
DSN = os.getenv("POSTGRES_DSN")
if not DSN:
    print("POSTGRES_DSN not set")
    raise SystemExit(1)

# asyncpg expects a DSN without the +asyncpg driver hint
dsn = DSN.replace("+asyncpg", "")

import asyncpg

async def main():
    conn = await asyncpg.connect(dsn)
    try:
        tables = [
            'solicitacoes_reserva',
            'cancelamentos_reserva',
            'solicitacoes_transferencia',
            'cancelamentos_transferencia',
        ]
        for t in tables:
            exists = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name=$1)", t)
            if not exists:
                print(f"{t}: NOT FOUND")
            else:
                cnt = await conn.fetchval(f"SELECT COUNT(*) FROM {t}")
                print(f"{t}: EXISTS, rows={cnt}")
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
