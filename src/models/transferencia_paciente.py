from typing_extensions import TypedDict


class TransferenciaPacienteInput(TypedDict):
    prontuario_paciente: int
    idade_paciente: int
    especialidade_paciente: str

class AceitarTransferenciaInput(TypedDict):
    leito_id: str
