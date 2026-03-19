from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
import os
import sys
# Ensure local package modules (e.g., `models`, `controllers`) are importable when running
# the app with uvicorn from the project root. This inserts `src/` into sys.path.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

from resources.database import DatabaseManager, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")

    # Initialize AGHU DB Manager and store in app.state
    aghu_dsn = os.getenv("POSTGRES_DSN")
    if aghu_dsn:
        app.state.aghu_db = DatabaseManager(aghu_dsn)
        print("AGHU PostgreSQL connection pool initialized.")
    else:
        print("WARNING: POSTGRES_DSN not found. Skipping AGHU DB initialization.")

    # Initialize App DB Manager (SQLite) and store in app.state
    app_dsn = os.getenv("SQLITE_DSN")
    sqlite_path = os.getenv("SQLITE_PATH")
    if not app_dsn and sqlite_path:
        app_dsn = f"sqlite+aiosqlite:///{os.path.abspath(sqlite_path)}"
        print(f"INFO: Derived SQLITE_DSN from SQLITE_PATH={sqlite_path}")
    if not app_dsn:
        default_sqlite_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "app.db"))
        app_dsn = f"sqlite+aiosqlite:///{default_sqlite_path}"
        print(f"WARNING: SQLITE_DSN not found. Using default local SQLite at {default_sqlite_path}.")
    app.state.app_db = DatabaseManager(app_dsn)
    print("App SQLite connection pool initialized.")

    # Create tables for App DB (if they don't exist) - for development only, Alembic handles this in production
    async with app.state.app_db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("App SQLite tables checked/created.")

    yield

    # Shutdown
    print("Shutting down...")
    if hasattr(app.state, 'aghu_db') and app.state.aghu_db:
        await app.state.aghu_db.close_connection()
        print("AGHU PostgreSQL connection pool closed.")
    if hasattr(app.state, 'app_db') and app.state.app_db:
        await app.state.app_db.close_connection()
        print("App SQLite connection pool closed.")

app = FastAPI(
    title="Esqueleto de Aplicação Web Full-Stack",
    description="Aplicação Backend monolítica (API REST) em Python/FastAPI, com foco em acesso e agregação de dados heterogêneos.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS para desenvolvimento local (Vite + backend) e uso do API tester.
_default_cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
_configured_cors_origins = os.getenv("CORS_ALLOW_ORIGINS", ",".join(_default_cors_origins))
_cors_origins = [origin.strip() for origin in _configured_cors_origins.split(",") if origin.strip()]
if not _cors_origins:
    _cors_origins = _default_cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve o frontend Vue 3 empacotado
static_dir = "frontend/dist/assets"
if os.path.isdir(static_dir):
    app.mount("/assets", StaticFiles(directory=static_dir), name="assets")

@app.get("/")
async def serve_frontend():
    """
    Serve o arquivo index.html do frontend Vue.
    Try common build locations and return a helpful 404 if not found.
    """
    candidates = [
        os.path.join("frontend", "dist", "index.html"),
        os.path.join("frontend", "index.html"),
        os.path.join("src", "static", "dist", "index.html"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return FileResponse(path)
    # none found — return a clear error to avoid RuntimeError when FileResponse tries to open a missing file
    raise HTTPException(status_code=404, detail=f"Frontend index.html not found. Checked paths: {candidates}")

# Placeholder para incluir os roteadores da API

from routers import paciente, auth, admin, leito, care, solicitacao_leito, reservas, transferencia_paciente, notificacao, users
app.include_router(paciente.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(leito.router)
app.include_router(care.router)
app.include_router(solicitacao_leito.router)
app.include_router(reservas.router)
app.include_router(transferencia_paciente.router)
app.include_router(notificacao.router)
app.include_router(users.router)

# Exemplo:
# from .routers import aih, bpa, material
# app.include_router(aih.router)
# app.include_router(bpa.router)
# app.include_router(material.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
