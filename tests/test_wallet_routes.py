"""Testes de integração das rotas /wallet."""

PASSENGER = {"name": "Ana Silva", "phone": "923456789", "pin": "1234", "role": "PASSENGER"}
DRIVER = {"name": "Joao Manuel", "phone": "912345678", "pin": "4321", "role": "DRIVER"}


def _register(client, data) -> dict:
    r = client.post("/auth/register", json=data)
    assert r.status_code == 201, r.text
    return r.json()


def test_register_driver_gets_code(make_client):
    driver = _register(make_client(), DRIVER)
    assert driver["driver_code"]
    assert len(driver["driver_code"]) == 5


def test_register_passenger_has_no_code(make_client):
    passenger = _register(make_client(), PASSENGER)
    assert passenger["driver_code"] is None


def test_wallet_requires_auth(make_client):
    assert make_client().get("/wallet").status_code == 401


def test_find_existing_driver(make_client):
    passenger_c, driver_c = make_client(), make_client()
    _register(passenger_c, PASSENGER)
    driver = _register(driver_c, DRIVER)
    r = passenger_c.get(f"/wallet/driver/{driver['driver_code']}")
    assert r.status_code == 200, r.text
    assert r.json()["driver_code"] == driver["driver_code"]
    assert r.json()["name"] == "Joao Manuel"


def test_find_driver_is_case_insensitive(make_client):
    passenger_c, driver_c = make_client(), make_client()
    _register(passenger_c, PASSENGER)
    driver = _register(driver_c, DRIVER)
    r = passenger_c.get(f"/wallet/driver/{driver['driver_code'].lower()}")
    assert r.status_code == 200, r.text


def test_find_unknown_driver_404(make_client):
    client = make_client()
    _register(client, PASSENGER)
    assert client.get("/wallet/driver/ZZZZZ").status_code == 404


def test_find_driver_requires_auth(make_client):
    assert make_client().get("/wallet/driver/ABCDE").status_code == 401


def test_deposit_updates_balance(make_client):
    client = make_client()
    _register(client, PASSENGER)
    r = client.post("/wallet/deposit", json={"amount": 5000})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["balance"] == 5000
    assert body["transactions"][0]["type"] == "DEPOSIT"
    assert body["transactions"][0]["direction"] == "in"


def test_payment_flow_between_passenger_and_driver(make_client):
    passenger_c, driver_c = make_client(), make_client()
    _register(passenger_c, PASSENGER)
    driver = _register(driver_c, DRIVER)

    passenger_c.post("/wallet/deposit", json={"amount": 1000})
    pay = passenger_c.post(
        "/wallet/pay",
        json={"driver_code": driver["driver_code"], "amount": 200, "pin": "1234"},
    )
    assert pay.status_code == 201, pay.text
    assert pay.json()["balance"] == 800

    # O cobrador recebeu.
    driver_wallet = driver_c.get("/wallet").json()
    assert driver_wallet["balance"] == 200
    assert driver_wallet["transactions"][0]["direction"] == "in"


def test_payment_wrong_pin_401(make_client):
    passenger_c, driver_c = make_client(), make_client()
    _register(passenger_c, PASSENGER)
    driver = _register(driver_c, DRIVER)
    passenger_c.post("/wallet/deposit", json={"amount": 1000})
    r = passenger_c.post(
        "/wallet/pay",
        json={"driver_code": driver["driver_code"], "amount": 200, "pin": "0000"},
    )
    assert r.status_code == 401


def test_payment_unknown_driver_404(make_client):
    client = make_client()
    _register(client, PASSENGER)
    client.post("/wallet/deposit", json={"amount": 1000})
    r = client.post("/wallet/pay", json={"driver_code": "ZZZZZ", "amount": 200, "pin": "1234"})
    assert r.status_code == 404


def test_payment_insufficient_422(make_client):
    passenger_c, driver_c = make_client(), make_client()
    _register(passenger_c, PASSENGER)
    driver = _register(driver_c, DRIVER)
    r = passenger_c.post(
        "/wallet/pay",
        json={"driver_code": driver["driver_code"], "amount": 200, "pin": "1234"},
    )
    assert r.status_code == 422


def test_withdraw_requires_driver_role(make_client):
    client = make_client()
    _register(client, PASSENGER)
    client.post("/wallet/deposit", json={"amount": 1000})
    r = client.post("/wallet/withdraw", json={"amount": 100})
    assert r.status_code == 403


def test_deposit_requires_passenger_role(make_client):
    client = make_client()
    _register(client, DRIVER)
    r = client.post("/wallet/deposit", json={"amount": 1000})
    assert r.status_code == 403


def test_driver_withdraw_after_receiving(make_client):
    passenger_c, driver_c = make_client(), make_client()
    _register(passenger_c, PASSENGER)
    driver = _register(driver_c, DRIVER)
    passenger_c.post("/wallet/deposit", json={"amount": 1000})
    passenger_c.post(
        "/wallet/pay",
        json={"driver_code": driver["driver_code"], "amount": 500, "pin": "1234"},
    )
    r = driver_c.post("/wallet/withdraw", json={"amount": 300})
    assert r.status_code == 201, r.text
    assert r.json()["balance"] == 200


def test_idempotent_deposit_via_api(make_client):
    client = make_client()
    _register(client, PASSENGER)
    client.post("/wallet/deposit", json={"amount": 500, "idempotency_key": "k1"})
    r = client.post("/wallet/deposit", json={"amount": 500, "idempotency_key": "k1"})
    assert r.json()["balance"] == 500  # não duplicou
