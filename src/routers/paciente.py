import os
from fastapi import APIRouter, Depends
from typing import List

from controllers import paciente_controller
# Alteração: Importamos apenas a FÁBRICA
from dependencies import get_paciente_provider, get_leito_controller
from providers.interfaces.paciente_provider_interface import PacienteProviderInterface
from controllers.leitos_controller import LeitosController

from auth.auth import auth_handler

# O contrato atual nao deve forcar CSV. A estrategia vem do ambiente e
# assume Postgres por padrao, porque a origem oficial destes dados nao eh o CSV.
STRATEGY = os.getenv("PACIENTE_PROVIDER_TYPE", "POSTGRES")

router = APIRouter(
    prefix="/api/pacientes",
    tags=["Pacientes"],
    dependencies=[Depends(auth_handler.decode_token)]
)

@router.get("", response_model=List[dict])
async def listar_pacientes(
    # A estratégia do provider agora vem do ambiente, sem forçar CSV.
    provider: PacienteProviderInterface = Depends(get_paciente_provider(STRATEGY))
):
    """Lista todos os pacientes da fonte de dados configurada no roteador."""
    return await paciente_controller.listar_pacientes(provider)

@router.get("/{codigo}", response_model=dict)
async def obter_paciente(
    codigo: int,
    provider: PacienteProviderInterface = Depends(get_paciente_provider(STRATEGY))
):
    """Obtém um paciente pelo código a partir da fonte de dados configurada no roteador."""
    return await paciente_controller.obter_paciente_por_codigo(codigo, provider)

@router.get("/disponiveis/quantidade")
async def quantidade_leitos_disponiveis(
    controller: LeitosController = Depends(get_leito_controller)
):
    quantidade = await controller.quantidade_disponiveis()
    return {
        "quantidade_leitos_disponiveis": quantidade
    }
