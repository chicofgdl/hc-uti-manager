# Mapa de Requisições API (Frontend <-> Backend)

Última atualização: 24 Fev 2026

## 1. Requisições disparadas pelo frontend

| Método | URL | Frontend | Backend |
| --- | --- | --- | --- |
| `GET` | `/api/icu/beds` | `frontend/src/services/beds.ts` | `src/routers/care.py` |
| `GET` | `/api/icu/beds/available-count` | `frontend/src/services/beds.ts` | `src/routers/care.py` |
| `PATCH` | `/api/icu/beds/{bed_id}/availability` | `frontend/src/services/beds.ts` | `src/routers/care.py` |
| `GET` | `/api/icu/reservations` | `frontend/src/services/reservations.ts` | `src/routers/care.py` |
| `GET` | `/api/surgical-center/reservations` | `frontend/src/services/reservations.ts` | `src/routers/care.py` |
| `POST` | `/api/surgical-center/reservations` | `frontend/src/services/reservations.ts` | `src/routers/care.py` |
| `PATCH` | `/api/icu/reservations/{reservation_id}/decision` | `frontend/src/services/reservations.ts` | `src/routers/care.py` |
| `PATCH` | `/api/surgical-center/reservations/{reservation_id}/cancel` | `frontend/src/services/reservations.ts` | `src/routers/care.py` |
| `PATCH` | `/api/icu/reservations/{reservation_id}/cancel` | `frontend/src/services/reservations.ts` | `src/routers/care.py` |
| `GET` | `/api/icu/transfers` | `frontend/src/services/transfers.ts` | `src/routers/care.py` |
| `GET` | `/api/surgical-center/transfers` | `frontend/src/services/transfers.ts` | `src/routers/care.py` |
| `POST` | `/api/surgical-center/transfers` | `frontend/src/services/transfers.ts` | `src/routers/care.py` |
| `PATCH` | `/api/icu/transfers/{transfer_id}/decision` | `frontend/src/services/transfers.ts` | `src/routers/care.py` |
| `GET` | `/api/notifications` | `frontend/src/services/notifications.ts` | `src/routers/care.py` |
| `PATCH` | `/api/notifications/{notification_id}/read` | `frontend/src/services/notifications.ts` | `src/routers/care.py` |
| `PATCH` | `/api/notifications/read-all` | `frontend/src/services/notifications.ts` | `src/routers/care.py` |

## 2. Perfil ativo no frontend

- Controle visível no topo: `frontend/src/layouts/DefaultLayout.vue`.
- Perfis suportados:
  - `ICU` (UTI)
  - `SURGICAL_CENTER` (CC)
- Persistência do perfil: `localStorage` (`frontend/src/stores/role.ts`).
- Telas com regras por perfil:
  - Leitos: `frontend/src/views/Home.vue`
  - Reservas: `frontend/src/views/Solicitacoes.vue`
  - Transferências: `frontend/src/views/Altas.vue`

## 3. Implementação backend CSV-first

- Controller: `src/controllers/care_controller.py`
- Provider de negócio: `src/providers/implementations/app/care_provider.py`
- Serviço transacional CSV: `src/resources/care_csv_store.py`

## 4. Persistência e consistência de dados

- Toda mutação de leito/reserva/transferência escreve em:
  - `data/leitos.csv`
  - `data/pacientes.csv`
- Estratégia:
  - lock de concorrência por `.care_csv.lock`
  - escrita atômica por arquivo com `temp + os.replace`
  - rollback por backup em falha na atualização do par de CSVs

## 5. Endpoints legados mantidos

| Método | URL | Arquivo |
| --- | --- | --- |
| `GET` | `/leitos` | `src/routers/leito.py` |
| `GET` | `/leitos/disponiveis-para-reserva` | `src/routers/leito.py` |
| `POST` | `/leitos/{lto_lto_id}/reservar` | `src/routers/leito.py` |
| `POST` | `/leitos/{leito_id}/alta` | `src/routers/leito.py` |
| `DELETE` | `/leitos/{leito_id}/alta` | `src/routers/leito.py` |
