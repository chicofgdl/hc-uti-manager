# Glossary

## Business terms
| Termo | Definicao |
| --- | --- |
| `UTI` | Unidade de terapia intensiva. Role que decide disponibilidade de leito, reservas e transferencias. |
| `Centro Cirurgico` (`SURGICAL_CENTER`) | Role que solicita reserva e transferencia para UTI. |
| `Leito` | Recurso fisico da UTI representado por `BED` no dominio de cuidado. |
| `Reserva` | Solicitacao de bloqueio/alocacao de leito para paciente do centro cirurgico. |
| `Transferencia` | Solicita movimentacao do paciente do centro cirurgico para a UTI. |
| `Alta` | Indicacao de liberacao de um leito no fluxo legado `/leitos/*`. |
| `Prontuario` | Identificador externo do paciente (equivalente ao `patientId`/`external_id`). |
| `Intercorrencia` | Evento clinico/operacional que pode exigir cancelamento de disponibilidade, reserva ou transferencia. |

## Status and enums
| Termo | Definicao |
| --- | --- |
| `DISPONIVEL` | Leito liberado para ser reservado. |
| `NAO_DISPONIVEL` | Leito nao pode ser reservado no momento. |
| `LIVRE` | Leito sem paciente internado. |
| `OCUPADO` | Leito com paciente internado. |
| `PENDENTE` | Estado inicial de reserva/transferencia aguardando decisao da UTI. |
| `ACEITA` | Reserva/transferencia aprovada. |
| `NEGADA` | Reserva/transferencia recusada. |
| `CANCELADA` | Reserva/transferencia cancelada apos solicitacao. |

## Technical terms
| Termo | Definicao |
| --- | --- |
| `Provider` | Camada que encapsula acesso a dados e regras de persistencia. |
| `Controller` | Camada de orquestracao entre rota e provider. |
| `Router` | Camada HTTP (FastAPI) que expoe endpoints e valida payloads. |
| `Fallback` | Estrategia secundaria de dados (ex.: POSTGRES falha e usa CSV). |
| `Seed` | Carga inicial de dados no banco da aplicacao a partir de CSV. |
| `JWT` | Token de autenticacao Bearer de curta duracao para chamadas API. |
| `Refresh Token` | Token persistido em cookie HttpOnly para renovar access token. |
| `Role` | Papel de negocio para autorizacao e roteamento de notificacoes (`ICU` ou `SURGICAL_CENTER`). |
| `Legacy endpoints` | Endpoints antigos em `/leitos/*`, mantidos para compatibilidade. |
| `CSV-first` | Estrategia em que `leitos.csv` e `pacientes.csv` sao a fonte primária de estado operacional do fluxo UTI/CC. |
| `care_*` | Prefixo de colunas adicionadas aos CSVs para persistir estados de leito, reserva, transferencia e notificacao. |
| `Atomic write` | Escrita em arquivo temporario seguida de `replace`, evitando arquivo parcialmente gravado. |
| `Lock de concorrencia` | Exclusao mutua para impedir que duas requisicoes atualizem os CSVs ao mesmo tempo. |

## Where these terms appear
- Dominio e enums: `src/models/care.py`
- Contratos da API: `src/schemas/care.py`
- Regras de negocio: `src/providers/implementations/app/care_provider.py`
- Rotas de negocio UTI/CC: `src/routers/care.py`
