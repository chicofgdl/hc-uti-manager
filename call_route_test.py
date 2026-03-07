import sys, asyncio
sys.path.insert(0, 'src')
from routers import solicitacao_leito
from dependencies import get_solicitacao_reserva_controller

async def t():
    controller = get_solicitacao_reserva_controller(session=None)
    res = await solicitacao_leito.listar_todas(controller=controller)
    print('route result:', res)

asyncio.run(t())
