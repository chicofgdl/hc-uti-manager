from fastapi import APIRouter, Depends, status, HTTPException, Body, Request
import logging

from auth.auth import auth_handler
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
    _ = Depends(auth_handler.require_role("enfermeiro_cirurgia"))
):
    try:
        payload = await request.json()
        prontuario = payload.get("prontuario") or payload.get("prontuario_paciente")
        idade = payload.get("idade") or payload.get("idade_paciente")
        especialidade = payload.get("especialidade") or payload.get("especialidade_paciente")

        if not all([prontuario, idade, especialidade]):
            raise HTTPException(
                status_code=422,
                detail="Campos obrigatórios: prontuario, idade, especialidade"
            )

        created_id = await controller.criar({
            "prontuario": prontuario,
            "idade": idade,
            "especialidade": especialidade,
        })
        return {"message": "Solicitação criada com sucesso", "id": created_id}
    except HTTPException:
        raise
    except ValueError as e:
        logging.warning("Solicitacao de reserva duplicada/bloqueada: %s", e)
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logging.exception("ERROR in criar_solicitacao")
        raise HTTPException(status_code=500, detail=str(e))


# Listar todas
@router.get("")
async def listar_todas(
    controller: SolicitacaoReservaController = Depends(get_solicitacao_reserva_controller),
    _ = Depends(auth_handler.require_role("enfermeiro_uti"))
):
    try:
        return await controller.listar_todas()
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("ERROR in listar_todas")
        raise HTTPException(status_code=500, detail=str(e))


# Listar pendentes
@router.get("/pendentes")
async def listar_pendentes(
    controller: SolicitacaoReservaController = Depends(get_solicitacao_reserva_controller),
    _ = Depends(auth_handler.require_role("enfermeiro_uti"))
):
    try:
        return await controller.listar_pendentes()
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("ERROR in listar_pendentes")
        raise HTTPException(status_code=500, detail=str(e))


# Aprovar
@router.post("/{id}/aprovar")
async def aprovar(
    id: int,
    data: dict = Body(...),
    controller: SolicitacaoReservaController = Depends(get_solicitacao_reserva_controller),
    _ = Depends(auth_handler.require_role("enfermeiro_uti"))
):
    try:
        await controller.aprovar(id, data["lto_lto_id"])
        return {"message": "Solicitação aprovada"}
    except HTTPException:
        raise
    except ValueError as e:
        logging.warning("Invalid request in aprovar: %s", e)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.exception("ERROR in aprovar")
        raise HTTPException(status_code=500, detail=str(e))


# Negar
@router.post("/{id}/negar")
async def negar(
    id: int,
    data: dict | None = Body(None),
    controller: SolicitacaoReservaController = Depends(get_solicitacao_reserva_controller),
    _ = Depends(auth_handler.require_role("enfermeiro_uti"))
):
    try:
        await controller.negar(id, data.get("motivo") if data else None)
        return {"message": "Solicitação negada"}
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("ERROR in negar")
        raise HTTPException(status_code=500, detail=str(e))


# Cancelar (Centro Cirúrgico ou UTI)
@router.post("/{id}/cancelar")
async def cancelar(
    id: int,
    data: dict | None = Body(None),
    perfil_payload: dict = Depends(auth_handler.require_any_role(["enfermeiro_uti", "enfermeiro_cirurgia"])),
    controller: SolicitacaoReservaController = Depends(get_solicitacao_reserva_controller),
):
    try:
        await controller.cancelar(
            solicitacao_id=id,
            perfil=perfil_payload.get("username"),
            motivo=data.get("motivo") if data else None
        )
        return {"message": "Solicitação cancelada"}
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("ERROR in cancelar")
        raise HTTPException(status_code=500, detail=str(e))
