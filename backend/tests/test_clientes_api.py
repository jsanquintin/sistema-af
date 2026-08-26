import uuid
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.main import app
from app.models.cliente import Cliente
from app.models.usuario import Usuario


def _fake_usuario(empresa_id: int | None = None):
    return Usuario(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        empresa_id=empresa_id,
        email="facturacion@agrocasa.com",
        nombre_completo="Facturacion",
        hash_password="irrelevante-en-este-test",
        rol="facturacion",
        activo=True,
    )


def test_listar_clientes_requiere_autenticacion():
    client = TestClient(app)
    response = client.get("/clientes")
    assert response.status_code in (401, 403)


def test_crear_cliente_fija_tenant_id():
    usuario = _fake_usuario()
    fake_app_session = MagicMock()
    fake_app_session.refresh.side_effect = lambda obj: setattr(obj, "id", 1)

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=fake_app_session):
        client = TestClient(app)
        response = client.post("/clientes", json={"empresa_id": 11, "nombre": "Cafe Export SRL"})
    app.dependency_overrides.clear()

    assert response.status_code == 201
    creado = fake_app_session.add.call_args[0][0]
    assert isinstance(creado, Cliente)
    assert creado.tenant_id == usuario.tenant_id
    assert creado.pais == "República Dominicana"  # default aplicado


def test_crear_cliente_rechaza_empresa_no_autorizada():
    usuario = _fake_usuario(empresa_id=7)

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=MagicMock()):
        client = TestClient(app)
        response = client.post("/clientes", json={"empresa_id": 9, "nombre": "Cafe Export SRL"})
    app.dependency_overrides.clear()

    assert response.status_code == 403


def test_eliminar_cliente_devuelve_409_si_tiene_registros_asociados():
    from sqlalchemy.exc import IntegrityError

    usuario = _fake_usuario()
    fake_app_session = MagicMock()
    fake_app_session.get.return_value = Cliente(id=1, tenant_id=usuario.tenant_id, empresa_id=11, nombre="X")
    fake_app_session.commit.side_effect = IntegrityError("stmt", {}, Exception("fk violation"))

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=fake_app_session):
        client = TestClient(app)
        response = client.delete("/clientes/1")
    app.dependency_overrides.clear()

    assert response.status_code == 409
    fake_app_session.rollback.assert_called_once()
