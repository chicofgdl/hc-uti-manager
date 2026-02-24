# API Reference (CSV-first)

## Base URL
- Backend local: `http://localhost:8000`
- Frontend Vite proxy: `http://localhost:5173` (requisições para `/api/...`)

## Auth
- Rotas em `/api/...` usam Bearer token.
- Em desenvolvimento local: `AUTH_ENABLED=false` permite mock user.

## Fluxo UTI/CC

### Leitos (UTI)
| Método | URL | Descrição |
| --- | --- | --- |
| `GET` | `/api/icu/beds` | Lista todos os leitos do fluxo UTI/CC |
| `GET` | `/api/icu/beds/available-count` | Quantidade de leitos disponíveis para reserva |
| `PATCH` | `/api/icu/beds/{bed_id}/availability` | Disponibiliza ou cancela disponibilização de leito |

Payload:
```json
{
  "availableForReservation": true
}
```

### Reservas
| Método | URL | Descrição |
| --- | --- | --- |
| `POST` | `/api/surgical-center/reservations` | CC solicita reserva |
| `GET` | `/api/surgical-center/reservations` | Lista reservas (visão CC) |
| `GET` | `/api/icu/reservations` | Lista reservas (visão UTI) |
| `PATCH` | `/api/icu/reservations/{id}/decision` | UTI aceita/nega reserva |
| `PATCH` | `/api/surgical-center/reservations/{id}/cancel` | CC cancela solicitação/reserva |
| `PATCH` | `/api/icu/reservations/{id}/cancel` | UTI cancela solicitação/reserva |

Payload criação:
```json
{
  "patientId": "77001",
  "notes": "pós-operatório",
  "preferredDateTime": null
}
```

Payload decisão:
```json
{
  "decision": "ACCEPT",
  "bedId": 1
}
```

### Transferências (CC -> UTI)
| Método | URL | Descrição |
| --- | --- | --- |
| `POST` | `/api/surgical-center/transfers` | CC solicita transferência |
| `GET` | `/api/surgical-center/transfers` | Lista transferências (visão CC) |
| `GET` | `/api/icu/transfers` | Lista transferências (visão UTI) |
| `PATCH` | `/api/icu/transfers/{id}/decision` | UTI aceita/nega transferência |

Payload criação:
```json
{
  "patientId": "77001",
  "reservationId": 10,
  "bedId": null,
  "notes": "encaminhamento imediato"
}
```

### Notificações
| Método | URL | Descrição |
| --- | --- | --- |
| `GET` | `/api/notifications?role=ICU&unreadOnly=false` | Lista notificações por perfil |
| `PATCH` | `/api/notifications/{notification_id}/read` | Marca uma notificação como lida |
| `PATCH` | `/api/notifications/read-all?role=ICU` | Marca todas como lidas para o perfil |

## Regras de negócio aplicadas na API
- Leito só pode ser disponibilizado para reserva se estiver livre.
- Reserva aceita torna o leito indisponível para novas reservas.
- Uma reserva ativa (`PENDENTE`/`ACEITA`) por paciente.
- Uma transferência ativa (`PENDENTE`/`ACEITA`) por paciente.
- Aceite de transferência ocupa leito e move paciente para localização `UTI`.
- Negativas/cancelamentos limpam vínculos de leito/reserva/transferência.

## Persistência CSV obrigatória
- Cada ação atualiza `data/leitos.csv` e `data/pacientes.csv`.
- Escrita com lock de concorrência e atualização atômica por arquivo.
- Colunas `care_*` mantêm estado operacional sem remover colunas legadas.

Campos principais adicionados:
- `leitos.csv`:
  - `care_bed_id`
  - `care_base_availability_status`
  - `care_availability_status`
  - `care_occupancy_status`
  - `care_reserved_for_patient`
  - `care_current_patient`
- `pacientes.csv`:
  - `care_patient_id`
  - `care_location`
  - `care_current_bed_id`
  - `care_current_bed_code`
  - `care_reservations_json`
  - `care_transfers_json`

## Contratos e implementação
- Rotas: `src/routers/care.py`
- Schemas: `src/schemas/care.py`
- Regras: `src/providers/implementations/app/care_provider.py`
- Persistência CSV: `src/resources/care_csv_store.py`
