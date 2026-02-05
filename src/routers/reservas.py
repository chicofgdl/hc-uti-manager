from fastapi import APIRouter, Depends, status, HTTPException, Body
from typing import Any, Dict
from controllers.solicitacao_leitos_controller import SolicitacaoReservaController
from dependencies import get_solicitacao_reserva_controller

router = APIRouter(prefix="/reservas", tags=["Reservas"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def criar_reserva(
    data: dict = Body(...),
    controller: SolicitacaoReservaController = Depends(get_solicitacao_reserva_controller),
):
    prontuario = data.get("prontuario") or data.get("prontuario_paciente")
    idade = data.get("idade") or data.get("idade_paciente")
    especialidade = data.get("especialidade") or data.get("especialidade_paciente")

    if prontuario is None or idade is None or especialidade is None:
        raise HTTPException(status_code=422, detail="Missing required fields: prontuario, idade, especialidade")

    normalized = {
        "prontuario": prontuario,
        "idade": idade,
        "especialidade": especialidade,
    }

    await controller.criar(normalized)
    return {"message": "Reserva criada com sucesso"}
