import uuid
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.main import app
from app.models.obra import Obra
from app.models.sucursal import Sucursal
from app.models.usuario import Usuario


def _fake_usuario(empresa_id: int | None = None):
    return Usuario(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        empresa_id=empresa_id,
        email="contador@creixa.com",
        nombre_completo="Contador",
        hash_password="irrelevante-en-este-test",
        rol="contador",
        activo=True,
    )


def test_listar_obras_requiere_autenticacion():
    client = TestClient(app)
    response = client.get("/obras", params={"empresa_id": 1})
    assert response.status_code in (401, 403)


def test_crear_obra_fija_tenant_id_y_estado_inicial():
    usuario = _fake_usuario()
    sucursal = Sucursal(id=1, tenant_id=usuario.tenant_id, empresa_id=11, codigo="P1", nombre="Proyecto 1", tipo="proyecto")
    fake_app_session = MagicMock()
    fake_app_session.get.return_value = sucursal
    fake_app_session.refresh.side_effect = lambda obj: setattr(obj, "id", 1)

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=fake_app_session):
        client = TestClient(app)
        response = client.post(
            "/obras",
            json={
                "empresa_id": 11,
                "sucursal_id": 1,
                "cliente_id": 5,
                "codigo": "OBRA-2026-001",
                "nombre": "Torre Lincoln",
                "monto_contrato": 500000,
                "moneda": "DOP",
                "fecha_inicio": "2026-08-01",
            },
        )
    app.dependency_overrides.clear()

    assert response.status_code == 201
    creada = fake_app_session.add.call_args[0][0]
    assert isinstance(creada, Obra)
    assert creada.tenant_id == usuario.tenant_id
    assert creada.estado == "en_proceso"
    assert creada.costo_acumulado == 0
    assert creada.costo_reconocido == 0


def test_crear_obra_rechaza_sucursal_que_no_es_proyecto():
    usuario = _fake_usuario()
    sucursal = Sucursal(id=1, tenant_id=usuario.tenant_id, empresa_id=11, codigo="F1", nombre="Finca 1", tipo="finca")
    fake_app_session = MagicMock()
    fake_app_session.get.return_value = sucursal

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=fake_app_session):
        client = TestClient(app)
        response = client.post(
            "/obras",
            json={
                "empresa_id": 11,
                "sucursal_id": 1,
                "cliente_id": 5,
                "codigo": "OBRA-1",
                "nombre": "Torre Lincoln",
                "monto_contrato": 500000,
                "fecha_inicio": "2026-08-01",
            },
        )
    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert "proyecto" in response.json()["detail"]


def test_crear_obra_rechaza_empresa_no_autorizada():
    usuario = _fake_usuario(empresa_id=7)

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=MagicMock()):
        client = TestClient(app)
        response = client.post(
            "/obras",
            json={
                "empresa_id": 9,
                "sucursal_id": 1,
                "cliente_id": 5,
                "codigo": "OBRA-1",
                "nombre": "Torre Lincoln",
                "monto_contrato": 500000,
                "fecha_inicio": "2026-08-01",
            },
        )
    app.dependency_overrides.clear()

    assert response.status_code == 403
