from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from controllers.notificacao_controller import NotificacaoController
from dependencies import get_notificacao_controller
from auth.auth import auth_handler

router = APIRouter(prefix="/notificacoes", tags=["Notificações"])

@router.get("", response_model=List[Dict[str, Any]])
async def listar_notificacoes(
    token_data: dict = Depends(auth_handler.decode_token),
    controller: NotificacaoController = Depends(get_notificacao_controller)
):
    role = None
    groups = token_data.get("groups", [])
    if "enfermeiro_uti" in groups:
        role = "enfermeiro_uti"
    elif "enfermeiro_cirurgia" in groups:
        role = "enfermeiro_cirurgia"
    
    if not role:
        return []
    
    return await controller.listar_por_role(role)