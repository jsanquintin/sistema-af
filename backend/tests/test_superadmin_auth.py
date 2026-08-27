import uuid
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.core.deps import get_db
from app.core.security import create_superadmin_token, decode_access_token, hash_password
from app.main import app
from app.models.superadmin import Superadmin


def _fake_superadmin(email="root@sistema-af.com", password="clave-real", activo=True):
    return Superadmin(
        id=uuid.uuid4(),
        email=email,
        nombre_completo="Superadmin de Prueba",
        hash_password=hash_password(password),
        activo=activo,
    )


def _override_db_returning(superadmin: Superadmin | None):
    # login() prueba `usuarios` primero (lista vacia = "no es un usuario de
    # tenant") y recien despues `superadmins` -- un solo fake_db sirve para
    # ambas consultas porque son metodos distintos sobre el mismo mock.
    def _get_db_override():
        fake_db = MagicMock()
        fake_db.execute.return_value.scalars.return_value.all.return_value = []
        fake_db.execute.return_value.scalar_one_or_none.return_value = superadmin
        yield fake_db

    return _get_db_override


def test_login_succeeds_with_correct_credentials():
    superadmin = _fake_superadmin(password="clave-real")
    app.dependency_overrides[get_db] = _override_db_returning(superadmin)
    client = TestClient(app)

    response = client.post("/auth/login", json={"email": superadmin.email, "password": "clave-real"})

    app.dependency_overrides.clear()
    assert response.status_code == 200
    payload = decode_access_token(response.json()["access_token"])
    assert payload["kind"] == "superadmin"
    assert payload["sub"] == str(superadmin.id)
    assert "tenant_id" not in payload


def test_login_rejects_wrong_password():
    superadmin = _fake_superadmin(password="clave-real")
    app.dependency_overrides[get_db] = _override_db_returning(superadmin)
    client = TestClient(app)

    response = client.post("/auth/login", json={"email": superadmin.email, "password": "clave-incorrecta"})

    app.dependency_overrides.clear()
    assert response.status_code == 401


def test_login_rejects_unknown_email():
    app.dependency_overrides[get_db] = _override_db_returning(None)
    client = TestClient(app)

    response = client.post("/auth/login", json={"email": "nadie@sistema-af.com", "password": "cualquiera"})

    app.dependency_overrides.clear()
    assert response.status_code == 401


def test_superadmin_token_rejected_by_get_current_user():
    # Regresion: un JWT de superadmin (sin tenant_id) nunca debe servir
    # contra un endpoint tenant-scoped -- get_current_user exige
    # tenant_id y falla cerrado si falta.
    token = create_superadmin_token(superadmin_id=uuid.uuid4())
    client = TestClient(app)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
