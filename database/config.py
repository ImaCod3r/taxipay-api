"""Conexão com o banco de dados.

Produção (Vercel): PostgreSQL, resolvido a partir da connection string em
``DATABASE_URL``. Dev/testes: SQLite local, quando a variável não existe.

Os models falam com um ``DatabaseProxy``, então nada neles depende do banco
concreto — quem decide é ``init_database()`` (chamada no lifespan da app; os
testes trocam o proxy por um SQLite temporário antes disso).
"""

from peewee import DatabaseProxy, Model, SqliteDatabase
from playhouse.db_url import connect as connect_url
from playhouse.db_url import register_database
from playhouse.postgres_ext import Psycopg3Database
from playhouse.shortcuts import ReconnectMixin

from core.config import DATABASE_URL, SQLITE_PATH

db = DatabaseProxy()


class ReconnectPostgresqlDatabase(ReconnectMixin, Psycopg3Database):
    """Postgres (driver psycopg3) que reabre a conexão sozinho se ela caiu.

    Em serverless a instância dorme entre requisições e o servidor pode ter
    encerrado a conexão nesse meio-tempo; sem isso a primeira query depois da
    pausa falharia com ``OperationalError``.
    """


# Faz o db_url devolver essa classe para as URLs padrão (postgres[ql]://),
# que é o formato entregue por Neon/Supabase/Railway.
register_database(ReconnectPostgresqlDatabase, "postgres", "postgresql")


def _build_database():
    if DATABASE_URL:
        return connect_url(DATABASE_URL)
    return SqliteDatabase(SQLITE_PATH)


def init_database(force: bool = False):
    """Aponta o proxy para o banco concreto. Idempotente.

    Não sobrescreve um banco já configurado (é o que permite aos testes
    injetarem o SQLite deles antes da app subir).
    """
    if db.obj is None or force:
        db.initialize(_build_database())
    return db.obj


class BaseModel(Model):
    class Meta:
        database = db
