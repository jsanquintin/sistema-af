import uuid

import jwt
import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_is_not_plaintext():
    hashed = hash_password("clave-super-secreta")
    assert hashed != "clave-super-secreta"


def test_verify_password_accepts_correct_password():
    hashed = hash_password("clave-super-secreta")
    assert verify_password("clave-super-secreta", hashed) is True


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("clave-super-secreta")
    assert verify_password("otra-clave", hashed) is False


def test_access_token_roundtrip_contains_tenant_id():
    usuario_id = uuid.uuid4()
    tenant_id = uuid.uuid4()

    token = create_access_token(usuario_id=usuario_id, tenant_id=tenant_id, rol="contador")
    payload = decode_access_token(token)

    assert payload["sub"] == str(usuario_id)
    assert payload["tenant_id"] == str(tenant_id)
    assert payload["rol"] == "contador"


def test_decode_access_token_rejects_tampered_token():
    usuario_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    token = create_access_token(usuario_id=usuario_id, tenant_id=tenant_id, rol="contador")

    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")

    with pytest.raises(jwt.PyJWTError):
        decode_access_token(tampered)


def test_decode_access_token_rejects_expired_token(monkeypatch):
    from datetime import datetime, timedelta, timezone

    import app.core.security as security_module

    class _FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2020, 1, 1, tzinfo=timezone.utc)

    monkeypatch.setattr(security_module, "datetime", _FrozenDatetime)
    token = create_access_token(usuario_id=uuid.uuid4(), tenant_id=uuid.uuid4(), rol="admin")

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)
