import uuid
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.core.security import verify_password
from app.main import app
from app.models.usuario import Usuario


def _fake_usuario(rol: str = "admin"):
    return Usuario(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        empresa_id=None,
        email="admin@agrocasa.com",
        nombre_completo="Admin",
        hash_password="irrelevante-en-este-test",
        rol=rol,
        activo=True,
    )


def test_listar_usuarios_requiere_autenticacion():
    client = TestClient(app)
    response = client.get("/usuarios")
    assert response.status_code in (401, 403)


def test_listar_usuarios_rechaza_no_admin():
    usuario = _fake_usuario(rol="contador")

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=MagicMock()):
        client = TestClient(app)
        response = client.get("/usuarios")
    app.dependency_overrides.clear()

    assert response.status_code == 403


def test_listar_usuarios_devuelve_lista_sin_hash_password():
    admin = _fake_usuario()
    otro = Usuario(
        id=uuid.uuid4(), tenant_id=admin.tenant_id, empresa_id=11, email="contador@agrocasa.com",
        nombre_completo="Contador", hash_password="hash-secreto", rol="contador", activo=True,
    )
    fake_session = MagicMock()
    fake_session.execute.return_value.scalars.return_value.all.return_value = [otro]

    app.dependency_overrides[get_current_user] = lambda: admin
    with patch("app.core.deps.AppSessionLocal", return_value=fake_session):
        client = TestClient(app)
        response = client.get("/usuarios")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "hash_password" not in response.json()[0]


def test_restablecer_password_rechaza_no_admin():
    usuario = _fake_usuario(rol="contador")

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=MagicMock()):
        client = TestClient(app)
        response = client.post(f"/usuarios/{uuid.uuid4()}/restablecer-password", json={"nueva_password": "unaClaveSegura123"})
    app.dependency_overrides.clear()

    assert response.status_code == 403


def test_restablecer_password_actualiza_el_hash():
    admin = _fake_usuario()
    objetivo = Usuario(
        id=uuid.uuid4(), tenant_id=admin.tenant_id, empresa_id=11, email="contador@agrocasa.com",
        nombre_completo="Contador", hash_password="hash-viejo", rol="contador", activo=True,
    )
    fake_session = MagicMock()
    fake_session.get.return_value = objetivo

    app.dependency_overrides[get_current_user] = lambda: admin
    with patch("app.core.deps.AppSessionLocal", return_value=fake_session):
        client = TestClient(app)
        response = client.post(
            f"/usuarios/{objetivo.id}/restablecer-password", json={"nueva_password": "unaClaveSegura123"}
        )
    app.dependency_overrides.clear()

    assert response.status_code == 204
    assert objetivo.hash_password != "hash-viejo"
    assert verify_password("unaClaveSegura123", objetivo.hash_password)


def test_restablecer_password_usuario_inexistente_devuelve_404():
    admin = _fake_usuario()
    fake_session = MagicMock()
    fake_session.get.return_value = None

    app.dependency_overrides[get_current_user] = lambda: admin
    with patch("app.core.deps.AppSessionLocal", return_value=fake_session):
        client = TestClient(app)
        response = client.post(f"/usuarios/{uuid.uuid4()}/restablecer-password", json={"nueva_password": "unaClaveSegura123"})
    app.dependency_overrides.clear()

    assert response.status_code == 404


def test_restablecer_password_rechaza_password_corta():
    admin = _fake_usuario()

    app.dependency_overrides[get_current_user] = lambda: admin
    with patch("app.core.deps.AppSessionLocal", return_value=MagicMock()):
        client = TestClient(app)
        response = client.post(f"/usuarios/{uuid.uuid4()}/restablecer-password", json={"nueva_password": "corta"})
    app.dependency_overrides.clear()

    assert response.status_code == 422
