from fastapi import APIRouter, Depends, Body
from typing import Optional

from ..controllers.transferencia_paciente_controller import (
    TransferenciaPacienteController
)
from ..dependencies import get_transferencia_paciente_controller
from ..models.transferencia import (
    TransferenciaPacienteInput,
    AceitarTransferenciaInput
)

router = APIRouter(
    prefix="/transferencias",
    tags=["Transferências"]
)

@router.post("")
async def criar_transferencia(
    data: TransferenciaPacienteInput,
    controller: TransferenciaPacienteController = Depends(
        get_transferencia_paciente_controller
    )
):
    await controller.criar(data)
    return {
        "message": "Solicitação de transferência criada com sucesso"
    }

@router.get("")
async def listar_transferencias(
    controller: TransferenciaPacienteController = Depends(
        get_transferencia_paciente_controller
    )
):
    return await controller.listar()

@router.post("/{transferencia_id}/aceitar")
async def aceitar_transferencia(
    transferencia_id: int,
    data: AceitarTransferenciaInput,
    controller: TransferenciaPacienteController = Depends(
        get_transferencia_paciente_controller
    )
):
    await controller.aceitar(
        transferencia_id=transferencia_id,
        leito_id=data["leito_id"]
    )
    return {
        "message": "Transferência aceita e paciente alocado no leito"
    }

@router.post("/{transferencia_id}/negar")
async def negar_transferencia(
    transferencia_id: int,
    motivo: Optional[str] = Body(default=None, embed=True),
    controller: TransferenciaPacienteController = Depends(
        get_transferencia_paciente_controller
    )
):
    await controller.negar(
        transferencia_id=transferencia_id,
        motivo=motivo
    )
    return {
        "message": "Transferência negada"
    }
