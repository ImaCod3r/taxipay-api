"""Fixtures compartilhadas: banco isolado e cliente HTTP."""

import os
import tempfile

import pytest

from database.config import db
from models.ledger import LedgerEntry
from models.notification import Notification
from models.user import User

VALID_REGISTER = {
    "name": "Ana Silva",
    "phone": "923456789",
    "pin": "1234",
    "role": "PASSENGER",
}


@pytest.fixture(scope="session", autouse=True)
def _database():
    """Aponta o Peewee para um SQLite temporário só dos testes."""
    path = os.path.join(tempfile.gettempdir(), "taxipay_pytest.db")
    if os.path.exists(path):
        os.remove(path)

    db.init(path)
    db.connect()
    db.create_tables([User, LedgerEntry, Notification])
    yield
    if not db.is_closed():
        db.close()
    # No Windows o arquivo pode ficar travado por conexões abertas nas threads
    # do TestClient; ignoramos e ele é recriado no próximo run.
    try:
        os.remove(path)
    except OSError:
        pass


@pytest.fixture(autouse=True)
def _clean_tables():
    """Garante isolamento: cada teste começa e termina com as tabelas vazias."""
    Notification.delete().execute()
    LedgerEntry.delete().execute()
    User.delete().execute()
    yield
    Notification.delete().execute()
    LedgerEntry.delete().execute()
    User.delete().execute()


@pytest.fixture
def client():
    """TestClient da app (tabelas já criadas pela fixture de banco)."""
    from fastapi.testclient import TestClient

    from main import app

    return TestClient(app)


@pytest.fixture
def make_client():
    """Cria clientes independentes (cookie jars separados) para vários usuários."""
    from fastapi.testclient import TestClient

    from main import app

    return lambda: TestClient(app)


@pytest.fixture
def registered_user(client):
    """Cria um usuário; o `client` fica autenticado via cookie. Devolve o usuário."""
    response = client.post("/auth/register", json=VALID_REGISTER)
    assert response.status_code == 201
    return response.json()
