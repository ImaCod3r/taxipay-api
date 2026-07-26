"""Conexão com o banco de dados.

Produção (Vercel): PostgreSQL, resolvido a partir da connection string em
``DATABASE_URL``. Dev/testes: SQLite local, quando a variável não existe.

Os models falam com um ``DatabaseProxy``, então nada neles depende do banco
concreto — quem decide é ``init_database()`` (chamada no lifespan da app; os
testes trocam o proxy por um SQLite temporário antes disso).
"""

from peewee import DatabaseProxy, InterfaceError, Model, OperationalError, SqliteDatabase
from playhouse.db_url import connect as connect_url
from playhouse.db_url import register_database
from playhouse.postgres_ext import Psycopg3Database

from core.config import DATABASE_URL, SQLITE_PATH

db = DatabaseProxy()


class ReconnectPostgresqlDatabase(Psycopg3Database):
    """Postgres (driver psycopg3) que reabre a conexão sozinho se ela caiu.

    Em serverless a instância dorme entre requisições e o servidor pode ter
    encerrado a conexão nesse meio-tempo; sem isso a primeira query depois da
    pausa falharia com ``OperationalError``.

    Não usamos o ``ReconnectMixin`` do playhouse: a lista de erros dele é de
    MySQL e o ``execute_sql`` dele não aceita o ``named_cursor`` que as bases
    ``postgres_ext`` passam.
    """

    # Erros que significam "a conexão morreu", e não "a query falhou".
    stale_connection_errors = (
        "server closed the connection",
        "connection already closed",
        "connection is closed",
        "connection not open",
        "terminating connection",
        "ssl connection has been closed",
        "consuming input failed",
        "no connection to the server",
        "eof detected",
    )

    def execute_sql(self, sql, params=None, **kwargs):
        return self._retry_once(super().execute_sql, sql, params, **kwargs)

    def begin(self, *args, **kwargs):
        return self._retry_once(super().begin, *args, **kwargs)

    def _retry_once(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (InterfaceError, OperationalError) as exc:
            # Dentro de uma transação reconectar perderia o que já foi escrito.
            if self.in_transaction() or not self._is_stale(exc):
                raise
            self._discard_connection()
            self.connect()
            return func(*args, **kwargs)

    def _is_stale(self, exc: Exception) -> bool:
        message = str(exc).lower()
        return any(fragment in message for fragment in self.stale_connection_errors)

    def _discard_connection(self) -> None:
        if self.is_closed():
            return
        try:
            self.close()
        except Exception:
            # A conexão já está inutilizável; basta limpar o estado do peewee.
            self._state.reset()


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
