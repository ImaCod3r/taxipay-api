"""Testes das notificações e da troca de PIN."""

PASSENGER = {"name": "Ana Silva", "phone": "923456789", "pin": "1234", "role": "PASSENGER"}
DRIVER = {"name": "Joao Manuel", "phone": "912345678", "pin": "4321", "role": "DRIVER"}


def _register(client, data) -> dict:
    r = client.post("/auth/register", json=data)
    assert r.status_code == 201, r.text
    return r.json()


def test_notifications_require_auth(make_client):
    assert make_client().get("/notifications").status_code == 401


def test_no_notifications_by_default(make_client):
    client = make_client()
    _register(client, PASSENGER)
    body = client.get("/notifications").json()
    assert body["notifications"] == []
    assert body["unread"] == 0


def test_payment_notifies_both_sides(make_client):
    passenger_c, driver_c = make_client(), make_client()
    _register(passenger_c, PASSENGER)
    driver = _register(driver_c, DRIVER)

    passenger_c.post("/wallet/deposit", json={"amount": 1000})
    pay = passenger_c.post(
        "/wallet/pay",
        json={"driver_code": driver["driver_code"], "amount": 200, "pin": "1234"},
    )
    assert pay.status_code == 201, pay.text

    payer = passenger_c.get("/notifications").json()
    assert payer["unread"] == 1
    assert payer["notifications"][0]["title"] == "Pagamento enviado"
    assert "200 Kz" in payer["notifications"][0]["body"]

    receiver = driver_c.get("/notifications").json()
    assert receiver["unread"] == 1
    assert receiver["notifications"][0]["title"] == "Pagamento recebido"


def test_mark_all_read(make_client):
    passenger_c, driver_c = make_client(), make_client()
    _register(passenger_c, PASSENGER)
    driver = _register(driver_c, DRIVER)
    passenger_c.post("/wallet/deposit", json={"amount": 1000})
    passenger_c.post(
        "/wallet/pay",
        json={"driver_code": driver["driver_code"], "amount": 200, "pin": "1234"},
    )

    assert passenger_c.post("/notifications/read").status_code == 204
    body = passenger_c.get("/notifications").json()
    assert body["unread"] == 0
    assert body["notifications"][0]["read"] is True


def test_change_pin_then_login_with_new(make_client):
    client = make_client()
    _register(client, PASSENGER)
    r = client.post("/auth/change-pin", json={"current_pin": "1234", "new_pin": "5678"})
    assert r.status_code == 204, r.text

    # PIN antigo falha, novo funciona.
    fresh = make_client()
    assert fresh.post("/auth/login", json={"phone": PASSENGER["phone"], "pin": "1234"}).status_code == 401
    assert fresh.post("/auth/login", json={"phone": PASSENGER["phone"], "pin": "5678"}).status_code == 200


def test_change_pin_wrong_current_401(make_client):
    client = make_client()
    _register(client, PASSENGER)
    r = client.post("/auth/change-pin", json={"current_pin": "0000", "new_pin": "5678"})
    assert r.status_code == 401


def test_change_pin_same_value_422(make_client):
    client = make_client()
    _register(client, PASSENGER)
    r = client.post("/auth/change-pin", json={"current_pin": "1234", "new_pin": "1234"})
    assert r.status_code == 422


def test_change_pin_requires_auth(make_client):
    r = make_client().post("/auth/change-pin", json={"current_pin": "1234", "new_pin": "5678"})
    assert r.status_code == 401
