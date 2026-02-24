# Architecture Overview (CSV-first MVP)

## Goal
Documentar a arquitetura atual do fluxo de leitos/reservas/transferências com persistência primária em CSV.

## High-level components
- Frontend Vue (`frontend/`) consome endpoints `/api/...`.
- Backend FastAPI (`src/`) expõe rotas de autenticação, pacientes, leitos legados e fluxo UTI/CC.
- Persistência operacional do domínio UTI/CC: `data/leitos.csv` + `data/pacientes.csv`.
- Serviço transacional CSV: `src/resources/care_csv_store.py`.

## Backend layers (fluxo UTI/CC)
- Router: `src/routers/care.py`
- Controller: `src/controllers/care_controller.py`
- Provider de negócio CSV-first: `src/providers/implementations/app/care_provider.py`
- Persistência transacional CSV: `src/resources/care_csv_store.py`

## CSV-first design
- Fonte de verdade operacional: somente `leitos.csv` e `pacientes.csv`.
- Lock de concorrência por arquivo de lock (`.care_csv.lock`) com exclusão mútua.
- Escrita atômica por arquivo (temp + `os.replace`) e rollback com backup se falhar entre os dois CSVs.
- Colunas `care_*` são adicionadas automaticamente sem remover colunas legadas.

## Estados e transições

### Leito
- Estados de disponibilidade:
  - `DISPONIVEL`
  - `NAO_DISPONIVEL`
- Estados de ocupação:
  - `LIVRE`
  - `OCUPADO`
- Regras:
  - Só disponibiliza para reserva se `LIVRE`.
  - Leito com reserva `ACEITA` fica indisponível para novas reservas.
  - Cancelar disponibilidade é bloqueado quando há vínculo ativo de reserva/transferência.

### Reserva
- Estados:
  - `PENDENTE` -> `ACEITA`
  - `PENDENTE` -> `NEGADA`
  - `PENDENTE|ACEITA` -> `CANCELADA`
- Regras:
  - Uma reserva `PENDENTE` ou `ACEITA` por paciente.
  - Aceite pode escolher leito explícito ou automático.
  - Negação/cancelamento limpam vínculo de leito.

### Transferência (CC -> UTI)
- Estados:
  - `PENDENTE` -> `ACEITA`
  - `PENDENTE` -> `NEGADA`
- Regras:
  - Uma transferência `PENDENTE` ou `ACEITA` por paciente.
  - Aceite ocupa leito e move paciente para localização `UTI`.
  - Negação limpa vínculo de leito.

## Sincronização entre CSVs
- `leitos.csv` recebe estado de disponibilidade/ocupação e vínculos de reserva/ocupação.
- `pacientes.csv` recebe localização do paciente, leito atual, histórico de reservas/transferências.
- Cada mutação é gravada nos dois CSVs dentro da mesma sessão de lock para evitar inconsistência operacional.

## Referências principais
- Rotas: `src/routers/care.py`
- Regras: `src/providers/implementations/app/care_provider.py`
- Persistência CSV: `src/resources/care_csv_store.py`
- Schemas API: `src/schemas/care.py`
