import uuid
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.main import app
from app.models.lote_cosecha import LoteCosecha
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


def test_listar_lotes_requiere_autenticacion():
    client = TestClient(app)
    response = client.get("/lotes-cosecha")
    assert response.status_code in (401, 403)


def test_crear_lote_fija_tenant_id_y_estado_default():
    usuario = _fake_usuario()
    fake_app_session = MagicMock()
    fake_app_session.refresh.side_effect = lambda obj: setattr(obj, "id", 1)

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=fake_app_session):
        client = TestClient(app)
        response = client.post(
            "/lotes-cosecha",
            json={
                "sucursal_id": 1,
                "producto": "cafe",
                "fecha_cosecha": "2026-08-20",
                "cantidad": 120.5,
            },
        )
    app.dependency_overrides.clear()

    assert response.status_code == 201
    creado = fake_app_session.add.call_args[0][0]
    assert isinstance(creado, LoteCosecha)
    assert creado.tenant_id == usuario.tenant_id
    assert creado.estado == "disponible"
    assert creado.unidad == "qq"


def test_crear_lote_rechaza_producto_faltante():
    app.dependency_overrides[get_current_user] = lambda: _fake_usuario()
    with patch("app.core.deps.AppSessionLocal", return_value=MagicMock()):
        client = TestClient(app)
        response = client.post(
            "/lotes-cosecha",
            json={"sucursal_id": 1, "fecha_cosecha": "2026-08-20", "cantidad": 10},
        )
    app.dependency_overrides.clear()

    assert response.status_code == 422
