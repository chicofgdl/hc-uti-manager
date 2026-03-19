from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from controllers.user_controller import UserController
from dependencies import get_user_controller

router = APIRouter(prefix="/users", tags=["Users"])

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str  # "enfermeiro_uti" or "enfermeiro_cirurgia"

@router.post("/register")
async def register_user(
    request: RegisterRequest,
    controller: UserController = Depends(get_user_controller)
):
    try:
        await controller.register(request.username, request.password, request.role)
        return {"message": "Usuário registrado com sucesso"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno")