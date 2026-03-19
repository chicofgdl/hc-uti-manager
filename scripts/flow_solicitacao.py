import os
import asyncio
from dotenv import load_dotenv
load_dotenv()
DSN = os.getenv('POSTGRES_DSN')
if not DSN:
    print('POSTGRES_DSN not set')
    raise SystemExit(1)

import asyncpg
import requests

dsn = DSN.replace('+asyncpg','')
API = 'http://127.0.0.1:8000'

async def ensure_leito(conn, lto='L200'):
    await conn.execute('''
        INSERT INTO leitos (lto_lto_id, status, tipo, alta_solicitada, atualizado_em)
        VALUES ($1, 'DISPONIVEL', 'UTI', false, NOW())
        ON CONFLICT (lto_lto_id) DO NOTHING
    ''', lto)

async def get_solicitacoes_db(conn):
    rows = await conn.fetch('SELECT id, status, prontuario_paciente, lto_lto_id FROM solicitacoes_reserva ORDER BY id')
    return [dict(r) for r in rows]

async def main():
    conn = await asyncpg.connect(dsn)
    try:
        lto = 'L200'
        print('Ensuring leito', lto)
        await ensure_leito(conn, lto)

        # 1) create solicitacao
        print('\nPOST /solicitacoes-reserva')
        r = requests.post(f'{API}/solicitacoes-reserva', json={'prontuario':'555','idade':55,'especialidade':'UTI'})
        print(r.status_code, r.text)

        # 2) list
        print('\nGET /solicitacoes-reserva')
        r = requests.get(f'{API}/solicitacoes-reserva')
        print(r.status_code, r.text)

        # 3) approve last id (pick highest id)
        rows = await get_solicitacoes_db(conn)
        if not rows:
            print('No solicitacoes found')
            return
        last = rows[-1]
        sid = last['id']
        print('\nApproving id', sid, 'to', lto)
        r = requests.post(f'{API}/solicitacoes-reserva/{sid}/aprovar', json={'lto_lto_id': lto})
        print(r.status_code, r.text)

        # 4) check DB
        rows = await get_solicitacoes_db(conn)
        print('\nDB rows after approve:')
        for r in rows:
            print(r)

        # 5) create another solicitacao and then negar
        print('\nCreating another solicitacao')
        r = requests.post(f'{API}/solicitacoes-reserva', json={'prontuario':'666','idade':66,'especialidade':'Clinica'})
        print(r.status_code, r.text)
        rows = await get_solicitacoes_db(conn)
        sid2 = rows[-1]['id']
        print('Negando id', sid2)
        r = requests.post(f'{API}/solicitacoes-reserva/{sid2}/negar', json={'motivo':'Teste'})
        print(r.status_code, r.text)

        rows = await get_solicitacoes_db(conn)
        print('\nDB rows after negar:')
        for r in rows:
            print(r)

        # 6) cancelar the approved one
        print('\nCanceling id', sid)
        # need to pass auth payload - endpoints use AuthHandler.decode_token in cancelar; but AUTH_ENABLED default is false so it won't require token
        r = requests.post(f'{API}/solicitacoes-reserva/{sid}/cancelar', json={'motivo':'Erro'},)
        print(r.status_code, r.text)

        rows = await get_solicitacoes_db(conn)
        print('\nDB rows after cancelar:')
        for r in rows:
            print(r)

    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
