import os
import asyncio
from dotenv import load_dotenv
load_dotenv()
DSN = os.getenv('POSTGRES_DSN')
if not DSN:
    print('POSTGRES_DSN not set')
    raise SystemExit(1)

import asyncpg
dsn = DSN.replace('+asyncpg','')
async def main():
    conn = await asyncpg.connect(dsn)
    try:
        rows = await conn.fetch("SELECT id, status, lto_lto_id FROM solicitacoes_reserva ORDER BY id")
        for r in rows:
            print(dict(r))
    finally:
        await conn.close()

if __name__=='__main__':
    asyncio.run(main())
