"""Aplicação FastAPI do Taxipay."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import AUTO_CREATE_TABLES
from database.config import db, init_database
from models.ledger import LedgerEntry
from models.notification import Notification
from models.user import User
from routers import auth, notifications, wallet

# Origens do frontend
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

MODELS = [User, LedgerEntry, Notification]

def init_db() -> None:
    """Resolve o banco (Postgres via DATABASE_URL) e garante as tabelas."""
    init_database()
    if not AUTO_CREATE_TABLES:
        return
    # Só devolvemos a conexão se fomos nós que a abrimos.
    was_open = not db.is_closed()
    db.connect(reuse_if_open=True)
    try:
        db.create_tables(MODELS, safe=True)
    finally:
        if not was_open and not db.is_closed():
            db.close()

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield
    if not db.is_closed():
        db.close()

app = FastAPI(title="Taxipay API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(wallet.router)
app.include_router(notifications.router)

@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
