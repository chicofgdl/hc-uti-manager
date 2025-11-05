# GEMINI.md: Esqueleto de Aplicação Web Full-Stack (Python/FastAPI)

## Instruções para o Agente de IA

> Este documento orienta a geração automática de uma aplicação **Python FastAPI** estruturada de forma monolítica, com frontend Vue 3 (Vite). Ele deve ser seguido à risca para garantir compatibilidade arquitetural e fidelidade funcional.
>
> - Gere a aplicação **seguindo exatamente os nomes de diretórios e arquivos** abaixo.
> - Use **async/await**, **type hints**, e **docstrings** no estilo Google.
> - Primeiro, gere a **estrutura completa** de diretórios e módulos; depois, implemente o conteúdo.
> - O frontend (Vue 3 + Vite) deve ser empacotado e servido por `FastAPI.staticfiles` na raiz `/`.
> - Gere exemplos mínimos de rotas e controllers para cada domínio, mesmo que com dados fictícios.
> - Use **snake_case** para Python e **camelCase** para TypeScript.

---

## 1. Visão Geral do Projeto

| Campo | Detalhe |
| :--- | :--- |
| **Nome do Projeto** | Esqueleto de Aplicação Web Full-Stack (Base para o Portal de Dados) |
| **Descrição Funcional** | Aplicação Backend monolítica (API REST) em Python/FastAPI, com foco em acesso e agregação de dados heterogêneos (sistemas hospitalares AGHU/Oracle, BI Metabase). Serve como base arquitetural replicável e hospeda o Frontend SPA (Vue 3/Vite). |
| **Pilha Tecnológica (TARGET)** | **Backend:** Python 3.10+, FastAPI, Uvicorn (ASGI). **ORM:** SQLAlchemy 2.0+ (ou Tortoise-ORM) com Alembic. **Frontend:** Vue 3, TypeScript, Vite. |
| **Pilha Tecnológica (SOURCE)** | Node.js (Express), TypeScript, Prisma ORM (SQLite), `pg` (PostgreSQL), `oracledb`. |
| **Arquitetura** | Arquitetura em Camadas com ênfase em Injeção de Dependência (FastAPI Depends). |
| **Serviço** | Servidor único (`src/main.py`) que expõe a API REST (`/api/*`) e serve o Frontend (raiz `/`). |

---

## 2. Estrutura Recomendada de Diretórios

```
src/
├── main.py
├── routers/
│   ├── aih.py
│   ├── bpa.py
│   └── material.py
├── controllers/
│   ├── aih_controller.py
│   ├── bpa_controller.py
│   └── material_controller.py
├── providers/
│   ├── aih_provider.py
│   ├── bpa_provider.py
│   └── material_provider.py
├── resources/
│   ├── database.py
│   ├── postgres.py
│   └── oracle.py
├── models/
│   ├── base.py
│   ├── link.py
│   └── manchete.py
├── helpers/
│   ├── csv_helper.py
│   ├── string_helper.py
│   ├── sql_helper.py
│   └── sigtap_helper.py
├── sql/
│   ├── bpa/
│   │   ├── consulta.sql
│   │   └── producao.sql
│   └── material/
│       └── estoque.sql
└── static/
    └── dist/   ← (build do Vue)
```

---

## 3. Arquitetura em Camadas e Fluxo de Dados (Fidelidade Arquitetural)

Fluxo obrigatório: **SQL → Resource → Provider → Controller → Router**.

| Camada | Diretório | Responsabilidade | Equivalente Source |
| :--- | :--- | :--- | :--- |
| **SQL Templates** | `sql/modulo/*.sql` | Código SQL nativo. Sem lógica de negócio. | `src/providers/SQL/*.sql` |
| **Resource** | `src/resources/database.py` | Gerencia pools e conexões assíncronas. | `resources/postgres.ts` |
| **Provider** | `src/providers/modulo_provider.py` | Executa SQL e retorna listas de dicionários. | `providers/BPAProvider.ts` |
| **Controller** | `src/controllers/modulo_controller.py` | Lógica de negócio e formatação final. | `controllers/bpaController.ts` |
| **Router** | `src/routers/modulo.py` | Define rotas HTTP e valida inputs (Pydantic). | `routes/bpa.ts` |

---

## 4. Pilha Tecnológica e Mapeamento de Dependências

| Categoria | Dependência Source | Dependência Target | Notas |
| :--- | :--- | :--- | :--- |
| **Framework** | `express`, `typescript` | `fastapi`, `uvicorn` | Tipagem Pydantic para Requests. |
| **DB PostgreSQL** | `pg` | `asyncpg`, `psycopg2` | Pools de conexão. |
| **DB Oracle** | `oracledb` | `python-oracledb` | DSN configurável. |
| **ORM Local** | `prisma`, `sqlite` | `SQLAlchemy 2.0+`, `alembic` | Migração do schema Prisma. |
| **Autenticação AD** | `activedirectory`, `passport-ad` | `python-ldap` | *Simple Bind*. |
| **Segurança JWT** | `jsonwebtoken` | `PyJWT` | Tokens de sessão. |
| **Upload** | `multer` | `python-multipart` | Upload multipart. |
| **CSV/Data** | `csvtojson`, `moment` | `csv`, `pandas`, `datetime` | Manipulação de dados. |

---

## 5. Segurança e Autenticação (Active Directory + JWT)

Implementar em `src/middlewares/auth.py`:

| Funcionalidade | Detalhes |
| :--- | :--- |
| **Autenticação AD** | Entrada: `name`, `password`. Usa `ldap.simple_bind_s(AD_URL)`. Retorna 403 em falha. |
| **Geração JWT** | Payload: `name`, `groups`. Expiração: 1 dia. |
| **Validação JWT** | `validate_jwt()` via `Depends()`. Verifica `Authorization: Bearer <token>`. Retorna 401 se inválido. |
| **Nível de Acesso** | Verifica grupos AD dentro do Controller. |

---

## 6. Persistência Local (Prisma → SQLAlchemy)

| Módulo | Fonte | Target | Modelos Críticos |
| :--- | :--- | :--- | :--- |
| **ORM** | `prisma.ts` | `SQLAlchemy ORM (async)` | `model Link`, `model Manchete` |
| **Migrações** | `prisma/migrations/*` | `alembic` | Estrutura replicada. |
| **Estratégia** | Converter `schema.prisma` → `models/*.py`. | Banco SQLite recriado. |

---

## 7. Helpers e Funções Críticas

| Arquivo | Função | Propósito |
| :--- | :--- | :--- |
| `sql_helper.py` | `create_query()` | Substitui placeholders (#startDate, #cod_prontuario). |
| `string_helper.py` | `remove_accents()`, `pad_start()`, `validate_cpf()` | Formatação e geração de arquivos magnéticos. |
| `csv_helper.py` | `convert_to_csv()`, `convert_to_tsv()` | Conversão JSON → CSV/TSV. |
| `sigtap_helper.py` | Lookup SIGTAP | Validação e enriquecimento de dados SUS. |

---

## 8. Domínios de Negócio e Escopo

| Domínio | Controllers/Providers | Função |
| :--- | :--- | :--- |
| **Faturamento SUS** | `aih_controller.py`, `bpa_controller.py` | Geração AIH, BPA, arquivos magnéticos. |
| **Inventário/Estoque** | `material_controller.py`, `material_estoque_controller.py` | Dados de estoque do AGHU/Oracle. |
| **Internação/Leitos** | `internacao_controller.py`, `leito_controller.py` | Censo, relatórios UTI/Clínica. |
| **Medicamentos** | `medicamentos_controller.py`, `antimicrobianos_controller.py` | Controle de dispensação. |
| **BI/Dashboard** | `metabase_controller.py` | Integração com Metabase. |
| **Utilitários** | `automacao_controller.py`, `upload_controller.py` | Automação e upload de arquivos. |
| **Prontuário** | `prontuario_controller.py`, `atendimento_controller.py` | Dados clínicos e históricos. |

---

## 9. Variáveis de Ambiente (.env.example)

```env
# Banco de Dados
POSTGRES_DSN=postgresql+asyncpg://user:password@host:5432/db
ORACLE_DSN=oracle+oracledb://user:password@host:1521/service

# Autenticação
AD_URL=ldap://ad.domain.local
JWT_SECRET=supersecretkey
JWT_EXP_HOURS=24

# Configurações Gerais
ENV=development
LOG_LEVEL=info
```

---

## 10. Output Esperado do Agente

1. Geração completa do esqueleto FastAPI com diretórios, módulos e placeholders.
2. Migração automática do schema Prisma para SQLAlchemy.
3. Implementação da autenticação LDAP + JWT.
4. Configuração de Alembic para migrações.
5. Implementação de 1 exemplo funcional por domínio (`bpa`, `aih`, `material`).
6. Servir o frontend Vue 3 pelo FastAPI (`/static/dist`).
7. Documentação automática de rotas via OpenAPI/Swagger.
