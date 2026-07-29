"""Testes de integração das rotas /auth via HTTP (auth por cookie)."""

import pytest

from core.config import COOKIE_NAME
from tests.conftest import VALID_REGISTER


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    # Identifica o código no ar (commit e banco em uso).
    assert body["commit"] and body["db"] == "SqliteDatabase"


def test_register_sets_cookie_and_hides_pin(client):
    r = client.post("/auth/register", json=VALID_REGISTER)
    assert r.status_code == 201, r.text
    body = r.json()
    # O corpo traz o usuário, NUNCA o token nem o PIN.
    assert body["name"] == "Ana Silva"
    assert body["role"] == "PASSENGER"
    assert "access_token" not in body
    assert "pin" not in body and "pin_hash" not in body
    # O token vai no cookie HttpOnly.
    assert r.cookies.get(COOKIE_NAME)
    set_cookie = r.headers.get("set-cookie", "")
    assert "httponly" in set_cookie.lower()


def test_register_duplicate_returns_409(client):
    client.post("/auth/register", json=VALID_REGISTER)
    r = client.post("/auth/register", json={**VALID_REGISTER, "name": "Outro"})
    assert r.status_code == 409
    assert "cadastrado" in r.json()["detail"]


@pytest.mark.parametrize(
    "override",
    [
        {"phone": "12345"},
        {"phone": "812345678"},
        {"pin": "12"},
        {"pin": "abcd"},
        {"name": "Al"},
        {"role": "ADMIN"},
    ],
)
def test_register_validation_returns_422(client, override):
    r = client.post("/auth/register", json={**VALID_REGISTER, **override})
    assert r.status_code == 422, r.text


def test_login_sets_cookie(client, registered_user):
    r = client.post("/auth/login", json={"phone": "923456789", "pin": "1234"})
    assert r.status_code == 200, r.text
    assert r.json()["phone"] == "923456789"
    assert r.cookies.get(COOKIE_NAME)


def test_login_wrong_pin_returns_401(client, registered_user):
    r = client.post("/auth/login", json={"phone": "923456789", "pin": "0000"})
    assert r.status_code == 401
    assert "incorretos" in r.json()["detail"]


def test_login_unknown_phone_returns_401(client):
    r = client.post("/auth/login", json={"phone": "999999999", "pin": "1234"})
    assert r.status_code == 401


def test_me_requires_authentication(client):
    assert client.get("/auth/me").status_code == 401


def test_me_rejects_invalid_token(client):
    r = client.get("/auth/me", headers={"Authorization": "Bearer abc.def.ghi"})
    assert r.status_code == 401


def test_me_returns_current_user_via_cookie(client, registered_user):
    # O cookie do registro já está no jar do client.
    r = client.get("/auth/me")
    assert r.status_code == 200, r.text
    assert r.json()["phone"] == "923456789"


def test_logout_clears_cookie(client, registered_user):
    assert client.get("/auth/me").status_code == 200
    logout = client.post("/auth/logout")
    assert logout.status_code == 204
    # Cookie removido => /me passa a negar.
    assert client.get("/auth/me").status_code == 401


# --- Sessão do app mobile (sem cookie jar): token no corpo + Bearer ---


def test_web_client_never_receives_token(client):
    """Sem `X-Client: mobile`, o JWT fica só no cookie HttpOnly."""
    r = client.post("/auth/register", json=VALID_REGISTER)
    assert r.status_code == 201, r.text
    assert r.json()["token"] is None
    assert r.cookies.get(COOKIE_NAME)


def test_mobile_client_receives_token_on_register(client):
    r = client.post("/auth/register", json=VALID_REGISTER, headers={"X-Client": "mobile"})
    assert r.status_code == 201, r.text
    assert r.json()["token"]


def test_mobile_client_receives_token_on_login(client, registered_user):
    r = client.post(
        "/auth/login",
        json={"phone": "923456789", "pin": "1234"},
        headers={"X-Client": "mobile"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["token"]


def test_mobile_token_authenticates_without_cookie(make_client):
    """O fluxo do app: regista, guarda o token e opera só com Bearer."""
    signup = make_client()
    token = signup.post(
        "/auth/register", json=VALID_REGISTER, headers={"X-Client": "mobile"}
    ).json()["token"]

    # Cliente novo => cookie jar vazio, tal como o app mobile.
    mobile = make_client()
    auth = {"Authorization": f"Bearer {token}"}

    assert mobile.get("/auth/me", headers=auth).json()["phone"] == "923456789"

    deposit = mobile.post(
        "/wallet/deposit", json={"amount": 5000, "idempotency_key": "dep-1"}, headers=auth
    )
    assert deposit.status_code == 201, deposit.text
    assert deposit.json()["balance"] == 5000


def test_mobile_deposit_without_token_is_rejected(make_client):
    make_client().post("/auth/register", json=VALID_REGISTER, headers={"X-Client": "mobile"})
    r = make_client().post("/wallet/deposit", json={"amount": 5000})
    assert r.status_code == 401
