import uuid
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.main import app
from app.models.almacen import Almacen
from app.models.sucursal import Sucursal
from app.models.usuario import Usuario


def _fake_usuario():
    return Usuario(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        empresa_id=None,
        email="contador@agrocasa.com",
        nombre_completo="Contador",
        hash_password="irrelevante-en-este-test",
        rol="contador",
        activo=True,
    )


def test_listar_almacenes_requiere_autenticacion():
    client = TestClient(app)
    response = client.get("/almacenes")
    assert response.status_code in (401, 403)


def test_crear_almacen_fija_tenant_id():
    usuario = _fake_usuario()
    fake_app_session = MagicMock()
    fake_app_session.refresh.side_effect = lambda obj: setattr(obj, "id", 1)

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=fake_app_session):
        client = TestClient(app)
        response = client.post("/almacenes", json={"sucursal_id": 1, "codigo": "A1", "nombre": "Bodega principal"})
    app.dependency_overrides.clear()

    assert response.status_code == 201
    creado = fake_app_session.add.call_args[0][0]
    assert isinstance(creado, Almacen)
    assert creado.tenant_id == usuario.tenant_id


def test_crear_almacen_rechaza_sucursal_de_otra_empresa():
    usuario = _fake_usuario()
    usuario.empresa_id = 7  # restringido a la empresa 7
    sucursal_ajena = Sucursal(id=1, tenant_id=uuid.uuid4(), empresa_id=9, codigo="S1", nombre="Ocoa", tipo="finca")
    fake_app_session = MagicMock()
    fake_app_session.get.return_value = sucursal_ajena

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=fake_app_session):
        client = TestClient(app)
        response = client.post("/almacenes", json={"sucursal_id": 1, "codigo": "A1", "nombre": "Bodega principal"})
    app.dependency_overrides.clear()

    assert response.status_code == 403


def test_desactivar_almacen_no_borra_la_fila():
    almacen = Almacen(id=1, tenant_id=uuid.uuid4(), sucursal_id=1, codigo="A1", nombre="Bodega", activo=True)
    sucursal = Sucursal(id=1, tenant_id=uuid.uuid4(), empresa_id=11, codigo="S1", nombre="Ocoa", tipo="finca")
    fake_app_session = MagicMock()
    fake_app_session.get.side_effect = lambda modelo, pk: {Almacen: almacen, Sucursal: sucursal}.get(modelo)

    app.dependency_overrides[get_current_user] = lambda: _fake_usuario()
    with patch("app.core.deps.AppSessionLocal", return_value=fake_app_session):
        client = TestClient(app)
        response = client.delete("/almacenes/1")
    app.dependency_overrides.clear()

    assert response.status_code == 204
    assert almacen.activo is False
    fake_app_session.delete.assert_not_called()
