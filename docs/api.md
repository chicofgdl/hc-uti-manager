# API Reference

Este arquivo documenta as rotas realmente montadas hoje em [`src/main.py`](/src/main.py).

## Base URL

- Backend local: `http://localhost:8000`
- Frontend Vite: `http://localhost:5173`
- No frontend, chamadas para `/api/...` passam pelo proxy do Vite quando ele está ativo.

## Autenticacao local

### Como o provider eh escolhido

- Se `AD_URL` estiver configurado no `.env`, a aplicacao tenta usar Active Directory.
- Se `AD_URL` e `AD_BASEDN` estiverem comentados, a aplicacao usa `MockAuthProvider`.

### Contas locais de teste

Com AD comentado:

- `admin / admin`
  - grupos: `GLO-SEC-HCPE-SETISD`, `Users`
- `uti / uti`
  - grupos: `enfermeiro_uti`
- `cirurgia / cirurgia`
  - grupos: `enfermeiro_cirurgia`

## Rotas atuais montadas

### Auth e usuario

| Metodo | URL | Auth | Observacao |
| --- | --- | --- | --- |
| `POST` | `/api/login` | Nao | Login por form-urlencoded |
| `POST` | `/api/token/refresh` | Cookie | Renova access token a partir do cookie `refresh_token` |
| `POST` | `/api/logout` | Cookie opcional | Invalida refresh token e limpa cookie |
| `GET` | `/api/users/me` | Bearer | Retorna o usuario decodificado do token |
| `GET` | `/api/admin-only-data` | Bearer admin | Exige grupo `GLO-SEC-HCPE-SETISD` |
| `POST` | `/users/register` | Nao | Cadastro local de usuario legado |

Payload de login:

```txt
Content-Type: application/x-www-form-urlencoded

username=admin
password=admin
remember_me=false
```

### Pacientes

Todas exigem Bearer token.

Observacao importante:

- Estas rotas nao usam CSV.
- Hoje a fonte oficial de `/api/pacientes` eh o banco da aplicacao (`data/app.db` / tabela `patients`), porque o Postgres do fluxo legado nao possui tabela de pacientes.
- O shape atual retornado e enxuto e pode conter campos nulos quando o banco nao tiver esses dados.

| Metodo | URL | Observacao |
| --- | --- | --- |
| `GET` | `/api/pacientes` | Lista pacientes a partir do banco da aplicacao |
| `GET` | `/api/pacientes/{codigo}` | Busca paciente por codigo a partir do banco da aplicacao |
| `GET` | `/api/pacientes/disponiveis/quantidade` | Quantidade de leitos disponiveis via `LeitosController` |

### Fluxo atual UTI / Centro Cirurgico

Estas sao as rotas do fluxo novo em [`src/routers/care.py`](/mnt/c/Users/F_Gabriel/OneDrive/Área%20de%20Trabalho/faculdade/Projetos/hc-uti-manager/src/routers/care.py).

Observacao importante:

- Todas exigem Bearer token.
- Hoje elas usam `decode_token`, mas nao fazem `require_role(...)` no roteador.
- Mesmo assim, funcionalmente o fluxo esperado eh:
  - Centro Cirurgico cria reservas e transferencias
  - UTI decide reservas e transferencias

#### Leitos

| Metodo | URL | Fluxo esperado |
| --- | --- | --- |
| `GET` | `/api/icu/beds` | UTI |
| `GET` | `/api/icu/beds/available-count` | UTI / apoio |
| `PATCH` | `/api/icu/beds/{bed_id}/availability` | UTI |

Payload:

```json
{
  "availableForReservation": true
}
```

#### Reservas

| Metodo | URL | Fluxo esperado |
| --- | --- | --- |
| `POST` | `/api/surgical-center/reservations` | Centro Cirurgico |
| `GET` | `/api/surgical-center/reservations` | Centro Cirurgico |
| `GET` | `/api/icu/reservations` | UTI |
| `PATCH` | `/api/icu/reservations/{reservation_id}/decision` | UTI |
| `PATCH` | `/api/surgical-center/reservations/{reservation_id}/cancel` | Centro Cirurgico |
| `PATCH` | `/api/icu/reservations/{reservation_id}/cancel` | UTI |

Payload de criacao:

```json
{
  "patientId": "77001",
  "notes": "pos-operatorio",
  "preferredDateTime": null
}
```

Payload de decisao:

```json
{
  "decision": "ACCEPT",
  "bedId": 1
}
```

Payload de cancelamento:

```json
{
  "reason": "Paciente reavaliado"
}
```

#### Transferencias

| Metodo | URL | Fluxo esperado |
| --- | --- | --- |
| `POST` | `/api/surgical-center/transfers` | Centro Cirurgico |
| `GET` | `/api/surgical-center/transfers` | Centro Cirurgico |
| `GET` | `/api/icu/transfers` | UTI |
| `PATCH` | `/api/icu/transfers/{transfer_id}/decision` | UTI |

Payload de criacao:

```json
{
  "patientId": "77001",
  "reservationId": 10,
  "bedId": null,
  "notes": "encaminhamento imediato"
}
```

Payload de decisao:

```json
{
  "decision": "ACCEPT",
  "bedId": 1
}
```

#### Notificacoes

| Metodo | URL | Observacao |
| --- | --- | --- |
| `GET` | `/api/notifications?role=ICU&unreadOnly=false` | Lista notificacoes por role |
| `PATCH` | `/api/notifications/{notification_id}/read` | Marca uma notificacao como lida |
| `PATCH` | `/api/notifications/read-all?role=ICU` | Marca todas como lidas |

## Rotas legadas ainda montadas

Estas rotas coexistem com o fluxo novo. Sao exatamente as que mais confundem o API tester hoje.

### Leitos legados

| Metodo | URL | Permissao |
| --- | --- | --- |
| `GET` | `/leitos` | `enfermeiro_uti` |
| `POST` | `/leitos/{lto_lto_id}/reservar` | `enfermeiro_cirurgia` |
| `POST` | `/leitos/{leito_id}/alta` | `enfermeiro_uti` |
| `DELETE` | `/leitos/{leito_id}/alta` | `enfermeiro_uti` |
| `GET` | `/leitos/disponiveis-para-reserva` | `enfermeiro_cirurgia` |
| `GET` | `/leitos/quantidade-disponiveis` | `enfermeiro_cirurgia` |

Observacao importante sobre o comportamento atual:

- Embora o contrato nomeie `POST /leitos/{leito_id}/alta` e `DELETE /leitos/{leito_id}/alta` como solicitacao/cancelamento de alta, no fluxo legado atual estas rotas estao sendo usadas como o mecanismo de disponibilizar e cancelar a disponibilizacao de um leito para reserva.
- Em termos de regra de negocio atual:
  - `POST /leitos/{leito_id}/alta` -> marca o leito como disponivel para reserva
  - `DELETE /leitos/{leito_id}/alta` -> remove essa disponibilidade para reserva
- Por isso, a conta `cirurgia` enxerga em `GET /leitos/disponiveis-para-reserva` apenas os leitos que a UTI marcou dessa forma.

### Solicitacoes de reserva legadas

| Metodo | URL | Permissao |
| --- | --- | --- |
| `POST` | `/solicitacoes-reserva` | `enfermeiro_cirurgia` |
| `GET` | `/solicitacoes-reserva` | `enfermeiro_uti` |
| `GET` | `/solicitacoes-reserva/pendentes` | `enfermeiro_uti` |
| `POST` | `/solicitacoes-reserva/{id}/aprovar` | `enfermeiro_uti` |
| `POST` | `/solicitacoes-reserva/{id}/negar` | `enfermeiro_uti` |
| `POST` | `/solicitacoes-reserva/{id}/cancelar` | `enfermeiro_uti` ou `enfermeiro_cirurgia` |

Payload de criacao:

```json
{
  "prontuario": "77001",
  "idade": 40,
  "especialidade": "Cardiologia"
}
```

Resposta atual de criacao:

```json
{
  "message": "Solicitação criada com sucesso",
  "id": 8
}
```

Observacao:

- O backend passou a devolver o `id` criado para viabilizar o cancelamento posterior da solicitacao pelo Centro Cirurgico.

### Reservas legadas

| Metodo | URL | Permissao |
| --- | --- | --- |
| `POST` | `/reservas` | `enfermeiro_cirurgia` |

Resposta atual de criacao:

```json
{
  "message": "Reserva criada com sucesso",
  "id": 8
}
```

### Transferencias legadas

| Metodo | URL | Permissao |
| --- | --- | --- |
| `POST` | `/transferencias` | `enfermeiro_cirurgia` |
| `GET` | `/transferencias` | `enfermeiro_uti` |
| `POST` | `/transferencias/{transferencia_id}/aceitar` | `enfermeiro_uti` |
| `POST` | `/transferencias/{transferencia_id}/negar` | `enfermeiro_uti` |

Payload de criacao:

```json
{
  "prontuario_paciente": 77001,
  "idade_paciente": 40,
  "especialidade_paciente": "Cardiologia"
}
```

### Notificacoes legadas

| Metodo | URL | Permissao |
| --- | --- | --- |
| `GET` | `/notificacoes` | Bearer; role inferida pelos grupos do token |

## O que no API tester eh legado

Arquivo: [`frontend/src/views/ApiYamlTester.vue`](/mnt/c/Users/F_Gabriel/OneDrive/Área%20de%20Trabalho/faculdade/Projetos/hc-uti-manager/frontend/src/views/ApiYamlTester.vue)

### Rotas do tester que batem no fluxo atual

- `/api/login`
- `/api/token/refresh`
- `/api/logout`
- `/api/users/me`
- `/api/admin-only-data`
- `/api/pacientes`
- `/api/pacientes/{codigo}`
- `/api/pacientes/disponiveis/quantidade`

### Rotas do tester que sao legadas

- `/leitos`
- `/leitos/{lto_lto_id}/reservar`
- `/leitos/{leito_id}/alta`
- `/leitos/disponiveis-para-reserva`
- `/leitos/quantidade-disponiveis`
- `/solicitacoes-reserva`
- `/solicitacoes-reserva/pendentes`
- `/solicitacoes-reserva/{id}/aprovar`
- `/solicitacoes-reserva/{id}/negar`
- `/solicitacoes-reserva/{id}/cancelar`
- `/reservas`
- `/transferencias`
- `/transferencias/{transferencia_id}/aceitar`
- `/transferencias/{transferencia_id}/negar`

### O que o tester nao cobre do fluxo atual

O tester nao cobre as rotas novas mais importantes do fluxo assistencial:

- `GET /api/icu/beds`
- `PATCH /api/icu/beds/{bed_id}/availability`
- `GET /api/icu/beds/available-count`
- `POST /api/surgical-center/reservations`
- `GET /api/surgical-center/reservations`
- `GET /api/icu/reservations`
- `PATCH /api/icu/reservations/{reservation_id}/decision`
- `PATCH /api/surgical-center/reservations/{reservation_id}/cancel`
- `PATCH /api/icu/reservations/{reservation_id}/cancel`
- `POST /api/surgical-center/transfers`
- `GET /api/surgical-center/transfers`
- `GET /api/icu/transfers`
- `PATCH /api/icu/transfers/{transfer_id}/decision`
- `GET /api/notifications`
- `PATCH /api/notifications/{notification_id}/read`
- `PATCH /api/notifications/read-all`

Motivo principal:

- o componente hoje so suporta `GET`, `POST` e `DELETE`
- o fluxo novo usa bastante `PATCH`

## Fonte de verdade

Se houver divergencia entre este documento, o API tester e o frontend, a fonte de verdade eh:

1. [`src/main.py`](/mnt/c/Users/F_Gabriel/OneDrive/Área%20de%20Trabalho/faculdade/Projetos/hc-uti-manager/src/main.py)
2. os roteadores em `src/routers/`
3. os schemas de `src/schemas/`
