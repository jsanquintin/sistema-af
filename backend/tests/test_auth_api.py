import uuid
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.core.deps import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.usuario import Usuario


def _fake_usuario(email="contador@agrocasa.com", password="clave-real", activo=True):
    return Usuario(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        empresa_id=None,
        email=email,
        nombre_completo="Contador de Prueba",
        hash_password=hash_password(password),
        rol="contador",
        activo=activo,
    )


def _override_db_returning(usuarios: list[Usuario]):
    def _get_db_override():
        fake_db = MagicMock()
        fake_db.execute.return_value.scalars.return_value.all.return_value = usuarios
        yield fake_db

    return _get_db_override


def test_login_succeeds_with_correct_credentials():
    usuario = _fake_usuario(password="clave-real")
    app.dependency_overrides[get_db] = _override_db_returning([usuario])
    client = TestClient(app)

    response = client.post("/auth/login", json={"email": usuario.email, "password": "clave-real"})

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_rejects_wrong_password():
    usuario = _fake_usuario(password="clave-real")
    app.dependency_overrides[get_db] = _override_db_returning([usuario])
    client = TestClient(app)

    response = client.post("/auth/login", json={"email": usuario.email, "password": "clave-incorrecta"})

    app.dependency_overrides.clear()
    assert response.status_code == 401


def test_login_rejects_unknown_email():
    app.dependency_overrides[get_db] = _override_db_returning([])
    client = TestClient(app)

    response = client.post("/auth/login", json={"email": "nadie@agrocasa.com", "password": "cualquiera"})

    app.dependency_overrides.clear()
    assert response.status_code == 401


def test_login_rejects_when_email_ambiguous_across_tenants():
    # email es unico por tenant, no globalmente -- si dos tenants
    # tuvieran el mismo email (hoy no aplica con un solo tenant activo,
    # pero el codigo debe fallar seguro y no elegir uno al azar).
    dup_a = _fake_usuario(password="clave-a")
    dup_b = _fake_usuario(password="clave-b")
    app.dependency_overrides[get_db] = _override_db_returning([dup_a, dup_b])
    client = TestClient(app)

    response = client.post("/auth/login", json={"email": dup_a.email, "password": "clave-a"})

    app.dependency_overrides.clear()
    assert response.status_code == 401


def test_me_requires_bearer_token():
    client = TestClient(app)
    response = client.get("/auth/me")
    assert response.status_code in (401, 403)


def test_me_rejects_token_for_wrong_tenant():
    usuario = _fake_usuario()
    otro_tenant_id = uuid.uuid4()
    # Token firmado con un tenant_id que no coincide con el del usuario real.
    token = create_access_token(usuario_id=usuario.id, tenant_id=otro_tenant_id, rol=usuario.rol)

    def _get_db_override():
        fake_db = MagicMock()
        fake_db.get.return_value = usuario
        yield fake_db

    app.dependency_overrides[get_db] = _get_db_override
    client = TestClient(app)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    app.dependency_overrides.clear()
    assert response.status_code == 401


def test_me_succeeds_with_valid_token():
    usuario = _fake_usuario()
    token = create_access_token(usuario_id=usuario.id, tenant_id=usuario.tenant_id, rol=usuario.rol)

    def _get_db_override():
        fake_db = MagicMock()
        fake_db.get.return_value = usuario
        yield fake_db

    app.dependency_overrides[get_db] = _get_db_override
    client = TestClient(app)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["email"] == usuario.email
