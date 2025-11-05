import pandas as pd
from typing import List, Dict, Any
from fastapi import HTTPException, status

from ..interfaces.paciente_provider_interface import PacienteProviderInterface

class PacienteCsvProvider(PacienteProviderInterface):
    def __init__(self, csv_path: str = 'data/pacientes.csv'):
        try:
            self.df = pd.read_csv(csv_path)
            # Garante que a coluna de código seja tratada como inteiro para comparações
            self.df['codigo'] = self.df['codigo'].astype(int)
        except FileNotFoundError:
            raise RuntimeError(f"Arquivo CSV de pacientes não encontrado em: {csv_path}")

    async def listar_pacientes(self) -> List[Dict[str, Any]]:
        return self.df.to_dict(orient='records')

    async def obter_paciente_por_codigo(self, codigo: int) -> Dict[str, Any]:
        paciente_df = self.df[self.df['codigo'] == codigo]
        if paciente_df.empty:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente não encontrado no CSV")
        
        # .to_dict('records') retorna uma lista, então pegamos o primeiro elemento
        return paciente_df.to_dict(orient='records')[0]
