# Esqueleto de Aplicação Web Full-Stack (Python/FastAPI + Vue.js)

Este projeto é um framework robusto e flexível para aplicações web modernas, construído com FastAPI no backend e Vue.js (Vite) no frontend. Ele foi projetado com uma arquitetura limpa e desacoplada, pronta para ser estendida e adaptada a diversas necessidades.

## ✨ Principais Características

- **Backend Moderno:** Construído com [FastAPI](https://fastapi.tiangolo.com/), oferecendo alta performance, código assíncrono e documentação de API automática (Swagger/OpenAPI).
- **Frontend Reativo:** Utiliza [Vue 3](https://vuejs.org/) com [Vite](https://vitejs.dev/) para uma experiência de desenvolvimento rápida e uma interface de usuário reativa.
- **Injeção de Dependência (DI):** Arquitetura de provedores flexível que permite trocar a fonte de dados (ex: PostgreSQL, CSV, Oracle) alterando apenas uma variável de ambiente, sem modificar o código de negócio.
- **Autenticação Segura:** Implementação de autenticação via Active Directory (AD) e gerenciamento de sessão com JSON Web Tokens (JWT), incluindo refresh tokens.
- **Estrutura Escalável:** Organização de projeto clara que separa responsabilidades (`routers`, `controllers`, `providers`), facilitando a manutenção e a adição de novas funcionalidades.

## 🛠️ Pilha Tecnológica

- **Backend:**
  - Python 3.10+
  - FastAPI (framework web)
  - Uvicorn (servidor ASGI)
  - SQLAlchemy (ORM para comunicação com banco de dados)
  - Alembic (migrações de banco de dados)
  - Pydantic (validação de dados)
  - python-ldap, PyJWT (autenticação e segurança)
- **Frontend:**
  - Vue 3 (Composition API)
  - Vite (build tool)
  - TypeScript
  - Axios (cliente HTTP)
  - TailwindCSS (estilização)

## 📂 Estrutura do Projeto

```
.
├── data/                 # Dados estáticos (ex: arquivos CSV)
├── frontend/             # Código-fonte da aplicação Vue.js
├── src/                  # Código-fonte do backend FastAPI
│   ├── auth/             # Lógica de autenticação (AD, JWT)
│   ├── controllers/      # Lógica de negócio
│   ├── dependencies.py   # Fábrica de injeção de dependência
│   ├── models/           # Modelos de dados (SQLAlchemy)
│   ├── providers/        # Camada de acesso a dados (Postgres, CSV, etc.)
│   │   ├── implementations/
│   │   └── interfaces/
│   ├── resources/        # Configuração de recursos (ex: conexão com DB)
│   └── routers/          # Definição dos endpoints da API
├── .env.example          # Arquivo de exemplo para variáveis de ambiente
├── README.md             # Esta documentação
└── requirements.txt      # Dependências do backend
```

## 🚀 Instalação e Execução

**Pré-requisitos:**
- Python 3.10 ou superior
- Node.js 18 ou superior
- Git

### 1. Configuração do Backend

```bash
# 1. Clone o repositório
# git clone <url-do-repositorio>
# cd <nome-do-repositorio>

# 2. Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate

# 3. Instale as dependências do Python
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env com suas configurações (banco de dados, segredos, etc.)
nano .env
```

### 2. Configuração do Frontend

```bash
# Em um novo terminal, navegue até a pasta do frontend
cd frontend

# Instale as dependências do Node.js
npm install
```

### 3. Executando a Aplicação

- **Para rodar o servidor backend:**
  ```bash
  # Na raiz do projeto, com o .venv ativado
  uvicorn src.main:app --reload
  ```
  O backend estará disponível em `http://127.0.0.1:8000`.
  A documentação interativa da API (Swagger) estará em `http://127.0.0.1:8000/docs`.

- **Para rodar o servidor de desenvolvimento do frontend:**
  ```bash
  # Na pasta frontend/
  npm run dev
  ```
  O frontend estará disponível em `http://127.0.0.1:5173` (ou outra porta indicada pelo Vite).

## 🔌 Arquitetura do Provedor de Dados

Uma das características centrais deste framework é a capacidade de alternar a fonte de dados dos pacientes dinamicamente.

Isso é controlado pela variável de ambiente `PACIENTE_PROVIDER_TYPE` no arquivo `.env`.

- **Para usar o banco de dados PostgreSQL:**
  `PACIENTE_PROVIDER_TYPE=POSTGRES`

- **Para usar o arquivo CSV local:**
  `PACIENTE_PROVIDER_TYPE=CSV`

O sistema foi projetado para que novas fontes de dados possam ser adicionadas implementando a `PacienteProviderInterface` e registrando a nova classe no `dependencies.py`.
