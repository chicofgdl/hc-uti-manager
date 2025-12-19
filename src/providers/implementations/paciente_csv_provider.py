import pandas as pd
import asyncio
import os
from typing import List, Dict, Any
from abc import ABC
from fastapi import HTTPException, status

from providers.interfaces.paciente_provider_interface import PacienteProviderInterface

class PacienteCsvProvider(PacienteProviderInterface):
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self._df: pd.DataFrame | None = None
        self._last_modified: float = 0.0
        self._lock = asyncio.Lock()

    async def _ler_csv(self) -> pd.DataFrame:
        df = pd.read_csv(self.csv_path)
        df = df.where(pd.notnull(df), None)
        return df

    async def _carregar(self):
        async with self._lock:
            modified = os.path.getmtime(self.csv_path)

            if self._df is not None and modified <= self._last_modified:
                return

            self._df = await asyncio.to_thread(self._ler_csv)
            self._last_modified = modified

    async def listar_pacientes(self) -> List[Dict[str, Any]]:
        await self._carregar()

        return [
            {
                "Prontuário": int(row["Prontuário"]),
                "Especialidade": row.get("Especialidade"),
                "Data Nasc.": row.get("Data Nasc.")
            }
            for _, row in self._df.iterrows()
        ]

    async def obter_paciente_por_codigo(self, codigo: int) -> Dict[str, Any]:
        await self._carregar()

        paciente_df = self._df[self._df["Prontuário"] == codigo]

        if paciente_df.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paciente não encontrado"
            )

        row = paciente_df.iloc[0]

        return {
            "Prontuário": int(row["Prontuário"]),
            "Especialidade": row.get("Especialidade"),
            "Data Nasc.": row.get("Data Nasc.")
        }