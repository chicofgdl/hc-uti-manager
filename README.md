# Esqueleto de Aplicacao Web Full-Stack (Python/FastAPI + Vue.js)

Este projeto e um framework robusto e flexivel para aplicacoes web modernas, construido com FastAPI no backend e Vue.js (Vite) no frontend. Ele foi projetado com uma arquitetura limpa e desacoplada, pronta para ser estendida e adaptada a diversas necessidades.

## Principais Caracteristicas

- **Backend Moderno:** Construido com FastAPI, oferecendo alta performance, codigo assincrono e documentacao de API automatica (Swagger/OpenAPI).
- **Frontend Reativo:** Utiliza Vue 3 com Vite para uma experiencia de desenvolvimento rapida e uma interface de usuario reativa.
- **Arquitetura de Provedores:** Design flexivel que permite trocar a fonte de dados de um dominio (ex: PostgreSQL, CSV) alterando uma unica variavel de configuracao no arquivo do roteador, sem modificar o codigo de negocio.
- **Autenticacao Hibrida:** Suporte nativo para autenticacao via Active Directory (AD) em producao e um provedor "mock" para desenvolvimento offline (sem necessidade de credenciais de AD).
- **Estrutura Escalavel:** Organizacao de projeto clara que separa responsabilidades (`routers`, `controllers`, `providers`), facilitando a manutencao e a adicao de novas funcionalidades.

## Estrutura do Projeto

A estrutura do projeto e projetada para separar claramente as responsabilidades entre backend, frontend e documentacao.

```
.
├── data/                 # Dados estaticos (ex: arquivos CSV)
├── docs/                 # Documentacao detalhada do projeto
│   ├── ARCHITECTURE.md   # Explicacao da arquitetura e padroes
│   ├── AUTHENTICATION.md # Detalhes sobre o sistema de autenticacao
│   └── SETUP.md          # Guia de instalacao e execucao
├── frontend/             # Codigo-fonte da aplicacao Vue.js
├── src/                  # Codigo-fonte do backend FastAPI
│   ├── auth/             # Logica de autenticacao (AD, Mock, JWT)
│   ├── controllers/      # Logica de negocio e orquestracao
│   ├── dependencies.py   # Fabrica de injecao de dependencia
│   ├── models/           # Modelos de dados (SQLAlchemy)
│   ├── providers/        # Camada de acesso a dados (Postgres, CSV, etc.)
│   │   ├── implementations/
│   │   └── interfaces/
│   ├── resources/        # Configuracao de recursos (ex: conexao com DB)
│   └── routers/          # Definicao dos endpoints da API
├── .env.example          # Arquivo de exemplo para variaveis de ambiente
└── README.md             # Esta documentacao
```

## Primeiros Passos

Para instalar e executar a aplicacao, siga o guia de configuracao detalhado:

- **[Guia de Instalacao e Execucao (SETUP.md)](./docs/SETUP.md)**

## Aprofundamento

Para entender a fundo os conceitos e padroes utilizados neste framework, consulte a documentacao especifica:

- **[Arquitetura do Projeto (ARCHITECTURE.md)](./docs/ARCHITECTURE.md)**
- **[Sistema de Autenticacao (AUTHENTICATION.md)](./docs/AUTHENTICATION.md)**

## Fluxos de UTI/Centro Cirúrgico implementados

- Modelagem persistida para leitos, reservas, transferências, pacientes e notificações com enums de status.
- Endpoints REST principais:
  - Leitos (UTI): `GET /api/icu/beds`, `PATCH /api/icu/beds/{id}/availability`, `GET /api/icu/beds/available-count`
  - Reservas (Centro Cirúrgico → UTI): `POST /api/surgical-center/reservations`, `PATCH /api/icu/reservations/{id}/decision`, `PATCH /api/*/reservations/{id}/cancel`
  - Transferências (Centro Cirúrgico → UTI): `POST /api/surgical-center/transfers`, `PATCH /api/icu/transfers/{id}/decision`
  - Notificações: `GET /api/notifications?role=ICU|SURGICAL_CENTER`, `PATCH /api/notifications/{id}/read`, `PATCH /api/notifications/read-all`
- Regras de negócio aplicadas: disponibilidade só em leito livre, impedimento de duplo agendamento, liberação de leito ao cancelar, aceitação de transferência ocupa leito e sinaliza paciente na UTI.
- Frontend Vue 3 integrado (Pinia + Axios) com:
  - Gestão de leitos (toggle de disponibilidade),
  - Reservas (solicitar, aceitar/negar, cancelar),
  - Transferências (solicitar, aceitar/negar),
  - Notificações em tempo quase real via polling (10s) e badge global.

## Contas locais de teste

Com `AD_URL` e `AD_BASEDN` comentados no `.env`, o backend usa o `MockAuthProvider`. Nesse modo:

- `admin / admin`: autenticacao e rotas administrativas.
- `uti / uti`: fluxos e permissoes da UTI.
- `cirurgia / cirurgia`: fluxos e permissoes do centro cirurgico.

As permissões do frontend passam a seguir automaticamente os grupos da conta autenticada.

## Rodando localmente (resumo)

```bash
# Backend
pip install -r requirements.txt
alembic upgrade head           # cria/atualiza schema
python -m src.seed             # popula leitos/pacientes de exemplo
uvicorn src.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Testes
pytest
```
