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


def test_listar_facturas_requiere_autenticacion():
    client = TestClient(app)
    response = client.get("/facturas", params={"empresa_id": 1})
    assert response.status_code in (401, 403)


def test_crear_factura_rechaza_empresa_no_autorizada():
    usuario = _fake_usuario(empresa_id=7)

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=MagicMock()):
        client = TestClient(app)
        response = client.post(
            "/facturas",
            json={
                "empresa_id": 9,
                "sucursal_id": 1,
                "cliente_id": 5,
                "tipo_factura": "local",
                "fecha_emision": "2026-08-26",
                "lineas": [{"descripcion": "Cafe qq", "cantidad": 10, "precio_unitario": 100}],
            },
        )
    app.dependency_overrides.clear()

    assert response.status_code == 403


def test_crear_factura_sin_secuencia_ecf_configurada_devuelve_400():
    usuario = _fake_usuario()
    cliente = Cliente(
        id=5, tenant_id=usuario.tenant_id, empresa_id=11, nombre="Cliente X", pais="RD", es_exterior=False,
        rnc_cedula="101-1",
    )
    fake_session = MagicMock()
    fake_session.get.side_effect = lambda modelo, pk: cliente if modelo is Cliente else None
    fake_session.execute.return_value.scalar_one_or_none.return_value = None

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=fake_session):
        client = TestClient(app)
        response = client.post(
            "/facturas",
            json={
                "empresa_id": 11,
                "sucursal_id": 1,
                "cliente_id": 5,
                "tipo_factura": "local",
                "fecha_emision": "2026-08-26",
                "lineas": [{"descripcion": "Cafe qq", "cantidad": 10, "precio_unitario": 100}],
            },
        )
    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert "secuencia e-CF" in response.json()["detail"]
