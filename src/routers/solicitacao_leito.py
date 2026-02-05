from fastapi import APIRouter, Depends, status, HTTPException, Body, Request

from auth.auth import AuthHandler
from controllers.solicitacao_leitos_controller import SolicitacaoReservaController
from dependencies import get_solicitacao_reserva_controller


router = APIRouter(
    prefix="/solicitacoes-reserva",
    tags=["Solicitações de Reserva"]
)

# Criar solicitação (Centro Cirúrgico)
@router.post("", status_code=status.HTTP_201_CREATED)
async def criar_solicitacao(
    request: Request,
    controller: SolicitacaoReservaController = Depends(get_solicitacao_reserva_controller),
):
    payload = await request.json()
    prontuario = payload.get("prontuario") or payload.get("prontuario_paciente")
    idade = payload.get("idade") or payload.get("idade_paciente")
    especialidade = payload.get("especialidade") or payload.get("especialidade_paciente")

    if not all([prontuario, idade, especialidade]):
        raise HTTPException(
            status_code=422,
            detail="Campos obrigatórios: prontuario, idade, especialidade"
        )

    await controller.criar({
        "prontuario": prontuario,
        "idade": idade,
        "especialidade": especialidade,
    })

    return {"message": "Solicitação criada com sucesso"}


# Listar todas
@router.get("")
async def listar_todas(
    controller: SolicitacaoReservaController = Depends(get_solicitacao_reserva_controller),
):
    return await controller.listar_todas()


# Listar pendentes
@router.get("/pendentes")
async def listar_pendentes(
    controller: SolicitacaoReservaController = Depends(get_solicitacao_reserva_controller),
):
    return await controller.listar_pendentes()


# Aprovar
@router.post("/{id}/aprovar")
async def aprovar(
    id: int,
    data: dict = Body(...),
    controller: SolicitacaoReservaController = Depends(get_solicitacao_reserva_controller),
):
    await controller.aprovar(id, data["lto_lto_id"])
    return {"message": "Solicitação aprovada"}


# Negar
@router.post("/{id}/negar")
async def negar(
    id: int,
    data: dict | None = Body(None),
    controller: SolicitacaoReservaController = Depends(get_solicitacao_reserva_controller),
):
    await controller.negar(id, data.get("motivo") if data else None)
    return {"message": "Solicitação negada"}


# Cancelar (Centro Cirúrgico ou UTI)
@router.post("/{id}/cancelar")
async def cancelar(
    id: int,
    data: dict | None = Body(None),
    perfil_payload: dict = Depends(AuthHandler.decode_token),
    controller: SolicitacaoReservaController = Depends(get_solicitacao_reserva_controller),
):
    await controller.cancelar(
        solicitacao_id=id,
        perfil=perfil_payload.get("username"),
        motivo=data.get("motivo") if data else None
    )
    return {"message": "Solicitação cancelada"}
