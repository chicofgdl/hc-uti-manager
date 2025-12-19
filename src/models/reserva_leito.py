from pydantic import BaseModel, Field

class ReservaLeitoInput(BaseModel):
    prontuario: int = Field(..., example=123456)
    idade: int = Field(..., example=65)
    especialidade: str = Field(..., example="Cardiologia")