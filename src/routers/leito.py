from fastapi import APIRouter, Depends, status
from controllers.leitos_controller import LeitosController
from models.reserva_leito import ReservaLeitoInput
from dependencies import get_leito_controller
from auth.auth import auth_handler
from typing import List, Dict, Any

router = APIRouter(prefix="/leitos", tags=["Leitos"])

@router.get("")
async def listar_leitos(
    controller: LeitosController = Depends(get_leito_controller),
    _ = Depends(auth_handler.require_role("enfermeiro_uti"))
):
    return await controller.listar()

@router.post("/{lto_lto_id}/reservar")
async def reservar_leito(
    lto_lto_id: str,
    payload: ReservaLeitoInput,
    controller: LeitosController = Depends(get_leito_controller),
    _ = Depends(auth_handler.require_role("enfermeiro_cirurgia"))
):
    return await controller.reservar(lto_lto_id, payload)

@router.post(
    "/{leito_id}/alta",
    status_code=status.HTTP_204_NO_CONTENT
)
async def solicitar_alta(
    leito_id: str,
    controller: LeitosController = Depends(get_leito_controller),
    _ = Depends(auth_handler.require_role("enfermeiro_uti"))
):
    await controller.solicitar_alta(leito_id)

@router.delete(
    "/{leito_id}/alta",
    status_code=status.HTTP_204_NO_CONTENT
)
async def cancelar_alta(
    leito_id: str,
    controller: LeitosController = Depends(get_leito_controller),
    _ = Depends(auth_handler.require_role("enfermeiro_uti"))
):
    await controller.cancelar_alta(leito_id) 

@router.get("/", response_model=List[Dict[str, Any]])
async def listar_leitos(
    controller: LeitosController = Depends(get_leito_controller),
    _ = Depends(auth_handler.require_role("enfermeiro_uti"))
):
    """
    Retorna todos os leitos cadastrados no banco B
    """
    return await controller.listar_leitos()

@router.get("/disponiveis-para-reserva")
async def listar_leitos_disponiveis_para_reserva(
    controller: LeitosController = Depends(get_leito_controller),
    _ = Depends(auth_handler.require_role("enfermeiro_cirurgia"))
):
    try:
        return await controller.listar_leitos_disponiveis_para_reserva()
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        # Print to server logs and return trace for debugging (remove in production)
        print("ERROR in listar_leitos_disponiveis_para_reserva:\n", tb)
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail={"error": str(e), "trace": tb})


@router.get("/quantidade-disponiveis")
async def quantidade_leitos_disponiveis(
    controller: LeitosController = Depends(get_leito_controller),
    _ = Depends(auth_handler.require_role("enfermeiro_cirurgia"))
):
    quantidade = await controller.quantidade_disponiveis()
    return {"quantidade_leitos_disponiveis": quantidade}