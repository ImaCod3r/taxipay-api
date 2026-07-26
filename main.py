"""Aplicação FastAPI do Taxipay."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.config import db
from models.ledger import LedgerEntry
from models.notification import Notification
from models.user import User
from routers import auth, notifications, wallet

# Origens do frontend 
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

def init_db() -> None:
    """Abre a conexão e garante as tabelas."""
    db.connect(reuse_if_open=True)
    db.create_tables([User, LedgerEntry, Notification])

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
