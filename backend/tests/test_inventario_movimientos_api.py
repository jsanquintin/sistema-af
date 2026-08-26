import uuid
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.main import app
from app.models.inventario_movimiento import InventarioMovimiento
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


def test_listar_movimientos_requiere_autenticacion():
    client = TestClient(app)
    response = client.get("/inventario-movimientos")
    assert response.status_code in (401, 403)


def test_crear_movimiento_entrada_fija_tenant_id():
    usuario = _fake_usuario()
    fake_app_session = MagicMock()
    fake_app_session.refresh.side_effect = lambda obj: setattr(obj, "id", 1)

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=fake_app_session):
        client = TestClient(app)
        response = client.post(
            "/inventario-movimientos",
            json={
                "lote_id": 1,
                "tipo_movimiento": "entrada",
                "almacen_destino_id": 1,
                "cantidad": 50,
                "fecha": "2026-08-20",
            },
        )
    app.dependency_overrides.clear()

    assert response.status_code == 201
    creado = fake_app_session.add.call_args[0][0]
    assert isinstance(creado, InventarioMovimiento)
    assert creado.tenant_id == usuario.tenant_id


def test_crear_movimiento_entrada_sin_almacen_destino_falla():
    app.dependency_overrides[get_current_user] = lambda: _fake_usuario()
    with patch("app.core.deps.AppSessionLocal", return_value=MagicMock()):
        client = TestClient(app)
        response = client.post(
            "/inventario-movimientos",
            json={"lote_id": 1, "tipo_movimiento": "entrada", "cantidad": 50, "fecha": "2026-08-20"},
        )
    app.dependency_overrides.clear()

    assert response.status_code == 422


def test_crear_movimiento_traslado_requiere_origen_y_destino():
    app.dependency_overrides[get_current_user] = lambda: _fake_usuario()
    with patch("app.core.deps.AppSessionLocal", return_value=MagicMock()):
        client = TestClient(app)
        response = client.post(
            "/inventario-movimientos",
            json={
                "lote_id": 1,
                "tipo_movimiento": "traslado",
                "almacen_origen_id": 1,
                "cantidad": 10,
                "fecha": "2026-08-20",
            },
        )
    app.dependency_overrides.clear()

    assert response.status_code == 422  # falta almacen_destino_id


def test_crear_movimiento_ajuste_no_exige_almacenes():
    usuario = _fake_usuario()
    fake_app_session = MagicMock()
    fake_app_session.refresh.side_effect = lambda obj: setattr(obj, "id", 1)

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=fake_app_session):
        client = TestClient(app)
        response = client.post(
            "/inventario-movimientos",
            json={"lote_id": 1, "tipo_movimiento": "ajuste", "cantidad": 5, "fecha": "2026-08-20"},
        )
    app.dependency_overrides.clear()

    assert response.status_code == 201
