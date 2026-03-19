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
        lto = 'L100'
        # insert minimal leito if not exists
        await conn.execute('''
            INSERT INTO leitos (lto_lto_id, status, tipo, alta_solicitada, atualizado_em)
            VALUES ($1, 'DISPONIVEL', 'UTI', false, NOW())
            ON CONFLICT (lto_lto_id) DO NOTHING
        ''', lto)
        print('Upserted leito', lto)
        row = await conn.fetchrow("SELECT * FROM leitos WHERE lto_lto_id=$1", lto)
        print(dict(row) if row else 'not found')
    finally:
        await conn.close()

if __name__=='__main__':
    asyncio.run(main())
