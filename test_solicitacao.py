import sys, asyncio
sys.path.insert(0, 'src')
from dependencies import get_solicitacao_reserva_controller

async def t():
    controller = get_solicitacao_reserva_controller(session=None)
    print('controller type:', type(controller))
    await controller.criar({'prontuario':123,'idade':50,'especialidade':'X'})
    res = await controller.listar_todas()
    print('listar_todas:', res)

asyncio.run(t())
