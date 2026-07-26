"""Configuração da aplicação, carregada do ambiente (.env)."""

import os

from dotenv import load_dotenv

load_dotenv()

# Chave de assinatura do JWT. DEFINA no .env em produção.
SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-troque-em-producao")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
# Sessão longa, típica de app mobile (30 dias).
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 30)))


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes"}


# ---- Cookie de autenticação (HttpOnly) ----
# O token vai num cookie HttpOnly (inacessível ao JS => resistente a XSS).
COOKIE_NAME: str = os.getenv("COOKIE_NAME", "tp_session")
# Em produção/HTTPS use COOKIE_SECURE=true. Em dev (http://localhost) fica false.
COOKIE_SECURE: bool = _as_bool(os.getenv("COOKIE_SECURE", "false"))
# "lax" no dev (front e back em localhost = mesmo site).
# Para app mobile/domínios diferentes: "none" (exige COOKIE_SECURE=true + HTTPS).
COOKIE_SAMESITE: str = os.getenv("COOKIE_SAMESITE", "lax").lower()
# Domínio opcional do cookie (ex.: ".taxipay.ao"). Vazio => host atual.
COOKIE_DOMAIN: str | None = os.getenv("COOKIE_DOMAIN") or None
COOKIE_MAX_AGE: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60
