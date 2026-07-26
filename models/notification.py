"""Notificações do usuário (ex.: pagamento enviado/recebido).

Simples e append-only: o backend cria as notificações e o frontend as busca
(polling) para exibir e disparar a notificação do sistema quando compilarmos
para mobile.
"""

from datetime import datetime

from peewee import BooleanField, CharField, DateTimeField, ForeignKeyField

from database.config import BaseModel
from models.user import User


class Notification(BaseModel):
    user = ForeignKeyField(User, backref="notifications", index=True, on_delete="CASCADE")
    title = CharField()
    body = CharField()
    read = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "notifications"
