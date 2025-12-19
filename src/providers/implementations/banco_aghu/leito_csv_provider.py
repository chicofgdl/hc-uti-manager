import pandas as pd
import asyncio
from datetime import datetime, date
from typing import List, Dict, Any
from providers.interfaces.leito_provider_interface import LeitoProviderInterface

class LeitoCsvProvider(LeitoProviderInterface):
    def __init__(self, leitos_csv: str, pacientes_csv: str):
        self.leitos_csv = leitos_csv
        self.pacientes_csv = pacientes_csv
        self._leitos_df = None
        self._pacientes_df = None

    async def _carregar_csvs(self):
        if self._leitos_df is not None:
            return

        def load():
            leitos = pd.read_csv(self.leitos_csv)
            pacientes = pd.read_csv(self.pacientes_csv)

            # Normalize patient identifier column: accept common variants and be tolerant
            candidate_cols = [
                "Prontuário", "Prontuario", "PRONTUARIO", "prontuário", "prontuario"
            ]
            source_col = None
            for c in candidate_cols:
                if c in pacientes.columns:
                    source_col = c
                    break

            if source_col is not None:
                try:
                    pacientes["Prontuário"] = pacientes[source_col].astype(int)
                except Exception as e:
                    # fallback: keep values as-is but warn
                    print(f"WARNING: failed to convert '{source_col}' to int: {e}")
                    pacientes["Prontuário"] = pacientes[source_col]
                try:
                    pacientes.set_index("Prontuário", inplace=True)
                except Exception as e:
                    print(f"WARNING: unable to set index on 'Prontuário': {e}")
            else:
                # If there is no patient identifier column, log and create an empty index so lookups are safe
                print("WARNING: pacientes CSV missing 'Prontuário' column; patient lookups will be disabled.")
                pacientes["Prontuário"] = pd.Series(dtype="Int64")
                pacientes.set_index("Prontuário", inplace=True)

            return leitos, pacientes

        self._leitos_df, self._pacientes_df = await asyncio.to_thread(load)

    def _calcular_idade(self, data_nasc: str | None) -> int | None:
        if not data_nasc:
            return None

        nascimento = datetime.strptime(data_nasc, "%d/%m/%Y").date()
        hoje = date.today()

        return hoje.year - nascimento.year - (
            (hoje.month, hoje.day) < (nascimento.month, nascimento.day)
        )

    def _pick(self, row: pd.Series, candidates: List[str], default=None):
        """Pick the first non-empty value from candidate column names in a row."""
        for c in candidates:
            val = None
            if c in row.index:
                val = row.get(c)
            if val is not None and (not (isinstance(val, float) and pd.isna(val))):
                return val
        return default

    async def listar_leitos(self) -> List[Dict[str, Any]]:
        await self._carregar_csvs()

        resultado = []

        for _, leito in self._leitos_df.iterrows():
            # column-name candidates for different CSV schemas
            lto_id = self._pick(leito, ["leito_numero", "Cód Leito", "CódLeito", "Cód-Leito"]) or None
            status = self._pick(leito, ["status", "Situação do Leito"]) or None
            tipo = self._pick(leito, ["tipo", "Tipo Leito"]) or None

            # patient fields
            prontuario = self._pick(leito, ["paciente_prontuario", "Prontuário", "Prontuario"]) or None
            prontuario_atual = int(prontuario) if (prontuario is not None and str(prontuario).strip() != "") else None

            idade_atual = None
            especialidade_atual = None
            paciente = None
            if prontuario_atual is not None and prontuario_atual in self._pacientes_df.index:
                paciente = self._pacientes_df.loc[int(prontuario_atual)]
                idade_atual = self._calcular_idade(paciente.get("Data Nasc.") if paciente is not None else None)
                especialidade_atual = paciente.get("Especialidade") if paciente is not None else None

            # next patient
            prontuario_proximo = self._pick(leito, ["proximo_prontuario", "prontuario_proximo", "prontuario_proximo"]) or None
            idade_proximo = None
            especialidade_proximo = self._pick(leito, ["proximo_especialidade", "especialidade_proximo"]) or None

            # updated timestamp
            atualizado_em = self._pick(leito, ["previsao_liberacao", "Data Última Atualização"]) or None

            # normalize alta flag: accept status == 'alta' or status == 'ALTA' or explicit column
            operacao = self._pick(leito, ["Operação", "operacao"]) or ""
            alta_solicitada = (str(status).strip().lower() == "alta") or (str(operacao).strip().upper() == "ALTA")

            resultado.append({
                "lto_lto_id": lto_id,
                "status": status,
                "tipo": tipo,
                "alta_solicitada": bool(alta_solicitada),

                "prontuario_atual": prontuario_atual,
                "idade_atual": idade_atual,
                "especialidade_atual": especialidade_atual,

                "prontuario_proximo": int(prontuario_proximo) if (prontuario_proximo is not None and str(prontuario_proximo).strip() != "") else None,
                "idade_proximo": idade_proximo,
                "especialidade_proximo": especialidade_proximo,

                "atualizado_em": atualizado_em
            })

        return resultado

    async def listar_leitos_disponiveis_para_reserva(self) -> List[Dict[str, Any]]:
        """Return leitos with alta_solicitada == True and without a next patient (CSV-backed)."""
        await self._carregar_csvs()

        resultado = []

        for _, leito in self._leitos_df.iterrows():
            try:
                # Determine status / operacao
                status = self._pick(leito, ["status", "Situação do Leito"]) or ""
                operacao = self._pick(leito, ["Operação", "operacao"]) or ""
                alta = (str(status).strip().lower() == "alta") or (str(operacao).strip().upper() == "ALTA")

                if not alta:
                    continue

                # Next patient (if any)
                prontuario_proximo = self._pick(leito, ["proximo_prontuario", "proximo_prontuario", "prontuario_proximo"]) or None
                if prontuario_proximo is not None and str(prontuario_proximo).strip() != "":
                    # has a next patient -> skip (we want available for reservation)
                    continue

                # Build the same shape as listar_leitos
                lto_id = self._pick(leito, ["leito_numero", "Cód Leito"]) or None
                tipo = self._pick(leito, ["tipo", "Tipo Leito"]) or None

                prontuario = self._pick(leito, ["paciente_prontuario", "Prontuário"]) or None
                prontuario_atual = int(prontuario) if (prontuario is not None and str(prontuario).strip() != "") else None

                paciente = None
                idade_atual = None
                especialidade_atual = None
                if prontuario_atual is not None and prontuario_atual in self._pacientes_df.index:
                    paciente = self._pacientes_df.loc[int(prontuario_atual)]
                    idade_atual = self._calcular_idade(paciente.get("Data Nasc.") if paciente is not None else None)
                    especialidade_atual = paciente.get("Especialidade") if paciente is not None else None

                atualizado_em = self._pick(leito, ["previsao_liberacao", "Data Última Atualização"]) or None

                resultado.append({
                    "lto_lto_id": lto_id,
                    "status": status,
                    "tipo": tipo,
                    "alta_solicitada": True,

                    "prontuario_atual": prontuario_atual,
                    "idade_atual": idade_atual,
                    "especialidade_atual": especialidade_atual,

                    "prontuario_proximo": None,
                    "idade_proximo": None,
                    "especialidade_proximo": None,

                    "atualizado_em": atualizado_em
                })
            except Exception:
                import traceback
                print("ERROR processing leitos CSV row:", traceback.format_exc())
        return resultado

    async def solicitar_alta(self, leito_id: int) -> None:
        """CSV provider cannot persist changes; this is a no-op with a warning."""
        print(f"WARNING: solicitar_alta called on CSV provider for leito_id={leito_id} (no-op)")

    async def cancelar_alta(self, leito_id: int) -> None:
        """CSV provider cannot persist changes; this is a no-op with a warning."""
        print(f"WARNING: cancelar_alta called on CSV provider for leito_id={leito_id} (no-op)")