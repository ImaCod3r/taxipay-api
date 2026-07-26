"""Ledger (livro-razão) financeiro — append-only e imutável.

Pilares aplicados:
- Cada movimento é uma linha; nada é atualizado/apagado (auditável).
- O saldo NUNCA é guardado: é sempre a soma das entradas do usuário.
- Valores em inteiros de Kz (sem ponto flutuante).
- Uma transferência (pagamento) gera duas linhas com a mesma `reference`
  (débito do pagador + crédito do recebedor) — partidas dobradas.
"""

from datetime import datetime
from enum import Enum

from peewee import CharField, DateTimeField, ForeignKeyField, IntegerField

from database.config import BaseModel
from models.user import User


class LedgerKind(str, Enum):
    DEPOSIT = "DEPOSIT"
    PAYMENT = "PAYMENT"
    WITHDRAWAL = "WITHDRAWAL"


class Direction(str, Enum):
    CREDIT = "CREDIT"  # entra (aumenta o saldo)
    DEBIT = "DEBIT"    # sai (diminui o saldo)


class LedgerEntry(BaseModel):
    user = ForeignKeyField(User, backref="ledger_entries", index=True, on_delete="CASCADE")
    # Agrupa as linhas de um mesmo evento (uuid).
    reference = CharField(index=True)
    kind = CharField(choices=[(k.value, k.value) for k in LedgerKind])
    direction = CharField(choices=[(d.value, d.value) for d in Direction])
    # Sempre positivo; o sinal vem da `direction`.
    amount = IntegerField()
    description = CharField()
    # Contraparte legível (ex.: código do cobrador, telefone do pagador).
    counterparty = CharField(null=True)
    # Chave de idempotência por usuário (evita cobrança/operação duplicada).
    idempotency_key = CharField(null=True, index=True)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "ledger_entries"
