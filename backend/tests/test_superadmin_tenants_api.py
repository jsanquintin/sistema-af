import uuid
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.core.deps import get_current_superadmin, get_db, get_superadmin_db
from app.core.security import create_access_token, decode_access_token
from app.main import app
from app.models.superadmin import Superadmin
from app.models.tenant import Tenant
from app.models.usuario import Usuario


def _fake_superadmin():
    return Superadmin(
        id=uuid.uuid4(),
        email="root@sistema-af.com",
        nombre_completo="Superadmin de Prueba",
        hash_password="irrelevante-en-este-test",
        activo=True,
    )


def _fake_tenant(nombre="Cliente Nuevo", activo=True):
    return Tenant(id=uuid.uuid4(), nombre=nombre, activo=activo)


def _fake_admin_usuario(tenant_id):
    return Usuario(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        empresa_id=None,
        email="admin@clientenuevo.com",
        nombre_completo="Admin Cliente Nuevo",
        hash_password="irrelevante-en-este-test",
        rol="admin",
        activo=True,
    )


def _override_superadmin_db(fake_db):
    def _override():
        yield fake_db

    return _override


def test_listar_tenants_requiere_autenticacion():
    client = TestClient(app)
    response = client.get("/superadmin/tenants")
    assert response.status_code in (401, 403)


def test_listar_tenants_rechaza_token_de_tenant_normal():
    # Un JWT de tenant normal (con tenant_id) tiene un shape distinto al
    # que exige get_current_superadmin (kind == "superadmin").
    token = create_access_token(usuario_id=uuid.uuid4(), tenant_id=uuid.uuid4(), rol="admin")
    client = TestClient(app)

    response = client.get("/superadmin/tenants", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_listar_tenants_devuelve_lista():
    superadmin = _fake_superadmin()
    tenants = [_fake_tenant("Agrocasa/Creixa"), _fake_tenant("Cliente Nuevo")]
    fake_db = MagicMock()
    fake_db.execute.return_value.scalars.return_value.all.return_value = tenants

    app.dependency_overrides[get_current_superadmin] = lambda: superadmin
    app.dependency_overrides[get_superadmin_db] = _override_superadmin_db(fake_db)
    client = TestClient(app)
    response = client.get("/superadmin/tenants")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert [t["nombre"] for t in response.json()] == ["Agrocasa/Creixa", "Cliente Nuevo"]


def test_crear_tenant_crea_tenant_y_primer_admin():
    superadmin = _fake_superadmin()
    fake_db = MagicMock()

    app.dependency_overrides[get_current_superadmin] = lambda: superadmin
    app.dependency_overrides[get_superadmin_db] = _override_superadmin_db(fake_db)
    client = TestClient(app)
    response = client.post(
        "/superadmin/tenants",
        json={
            "nombre": "Cliente Nuevo",
            "admin_email": "admin@clientenuevo.com",
            "admin_password": "unaClaveSegura123",
            "admin_nombre_completo": "Admin Cliente Nuevo",
        },
    )
    app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["tenant"]["nombre"] == "Cliente Nuevo"
    assert body["tenant"]["activo"] is True
    assert body["admin_email"] == "admin@clientenuevo.com"
    assert fake_db.add.call_count == 3  # tenant + usuario + superadmin_auditoria
    assert fake_db.commit.called


def test_crear_tenant_rechaza_password_corta():
    superadmin = _fake_superadmin()
    fake_db = MagicMock()

    app.dependency_overrides[get_current_superadmin] = lambda: superadmin
    app.dependency_overrides[get_superadmin_db] = _override_superadmin_db(fake_db)
    client = TestClient(app)
    response = client.post(
        "/superadmin/tenants",
        json={
            "nombre": "Cliente Nuevo",
            "admin_email": "admin@clientenuevo.com",
            "admin_password": "corta",
            "admin_nombre_completo": "Admin Cliente Nuevo",
        },
    )
    app.dependency_overrides.clear()

    assert response.status_code == 422


def test_actualizar_tenant_activa_y_desactiva():
    superadmin = _fake_superadmin()
    tenant = _fake_tenant(activo=True)
    fake_db = MagicMock()
    fake_db.get.return_value = tenant

    app.dependency_overrides[get_current_superadmin] = lambda: superadmin
    app.dependency_overrides[get_superadmin_db] = _override_superadmin_db(fake_db)
    client = TestClient(app)
    response = client.patch(f"/superadmin/tenants/{tenant.id}", json={"activo": False})
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["activo"] is False
    assert tenant.activo is False
    assert fake_db.commit.called


def test_actualizar_tenant_inexistente_devuelve_404():
    superadmin = _fake_superadmin()
    fake_db = MagicMock()
    fake_db.get.return_value = None

    app.dependency_overrides[get_current_superadmin] = lambda: superadmin
    app.dependency_overrides[get_superadmin_db] = _override_superadmin_db(fake_db)
    client = TestClient(app)
    response = client.patch(f"/superadmin/tenants/{uuid.uuid4()}", json={"activo": False})
    app.dependency_overrides.clear()

    assert response.status_code == 404


def test_entrar_a_tenant_devuelve_jwt_de_tenant_valido():
    superadmin = _fake_superadmin()
    tenant = _fake_tenant()
    admin = _fake_admin_usuario(tenant.id)
    fake_db = MagicMock()
    fake_db.get.return_value = tenant
    fake_db.execute.return_value.scalar_one_or_none.return_value = admin

    app.dependency_overrides[get_current_superadmin] = lambda: superadmin
    app.dependency_overrides[get_superadmin_db] = _override_superadmin_db(fake_db)
    client = TestClient(app)
    response = client.post(f"/superadmin/tenants/{tenant.id}/entrar")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = decode_access_token(response.json()["access_token"])
    assert payload["tenant_id"] == str(tenant.id)
    assert payload["sub"] == str(admin.id)
    assert payload["rol"] == "admin"
    assert payload["impersonated_by"] == str(superadmin.id)


def test_entrar_a_tenant_token_resultante_es_aceptado_por_get_current_user():
    # Integracion cruzada: el JWT que emite /entrar debe funcionar como
    # cualquier JWT de login normal en el resto del sistema.
    superadmin = _fake_superadmin()
    tenant = _fake_tenant()
    admin = _fake_admin_usuario(tenant.id)
    fake_superadmin_db = MagicMock()
    fake_superadmin_db.get.return_value = tenant
    fake_superadmin_db.execute.return_value.scalar_one_or_none.return_value = admin

    app.dependency_overrides[get_current_superadmin] = lambda: superadmin
    app.dependency_overrides[get_superadmin_db] = _override_superadmin_db(fake_superadmin_db)
    client = TestClient(app)
    entrar_response = client.post(f"/superadmin/tenants/{tenant.id}/entrar")
    app.dependency_overrides.clear()
    token = entrar_response.json()["access_token"]

    def _get_db_override():
        fake_db = MagicMock()
        fake_db.get.return_value = admin
        yield fake_db

    app.dependency_overrides[get_db] = _get_db_override
    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    app.dependency_overrides.clear()

    assert me_response.status_code == 200
    assert me_response.json()["id"] == str(admin.id)


def test_entrar_a_tenant_sin_admin_activo_devuelve_409():
    superadmin = _fake_superadmin()
    tenant = _fake_tenant()
    fake_db = MagicMock()
    fake_db.get.return_value = tenant
    fake_db.execute.return_value.scalar_one_or_none.return_value = None

    app.dependency_overrides[get_current_superadmin] = lambda: superadmin
    app.dependency_overrides[get_superadmin_db] = _override_superadmin_db(fake_db)
    client = TestClient(app)
    response = client.post(f"/superadmin/tenants/{tenant.id}/entrar")
    app.dependency_overrides.clear()

    assert response.status_code == 409


def test_entrar_a_tenant_inexistente_devuelve_404():
    superadmin = _fake_superadmin()
    fake_db = MagicMock()
    fake_db.get.return_value = None

    app.dependency_overrides[get_current_superadmin] = lambda: superadmin
    app.dependency_overrides[get_superadmin_db] = _override_superadmin_db(fake_db)
    client = TestClient(app)
    response = client.post(f"/superadmin/tenants/{uuid.uuid4()}/entrar")
    app.dependency_overrides.clear()

    assert response.status_code == 404
