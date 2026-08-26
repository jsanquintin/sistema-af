import uuid
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.main import app
from app.models.usuario import Usuario


def _fake_usuario(empresa_id: int | None = None):
    return Usuario(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        empresa_id=empresa_id,
        email="contador@agrocasa.com",
        nombre_completo="Contador",
        hash_password="irrelevante-en-este-test",
        rol="contador",
        activo=True,
    )


def test_balance_comprobacion_requiere_autenticacion():
    client = TestClient(app)
    response = client.get(
        "/reportes/balance-comprobacion",
        params={"empresa_id": 1, "desde": "2026-08-01", "hasta": "2026-08-31"},
    )
    assert response.status_code in (401, 403)


def test_balance_comprobacion_rechaza_empresa_no_autorizada():
    usuario = _fake_usuario(empresa_id=7)

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=MagicMock()):
        client = TestClient(app)
        response = client.get(
            "/reportes/balance-comprobacion",
            params={"empresa_id": 9, "desde": "2026-08-01", "hasta": "2026-08-31"},
        )
    app.dependency_overrides.clear()

    assert response.status_code == 403


def test_balance_comprobacion_agrega_por_cuenta():
    usuario = _fake_usuario()
    fake_session = MagicMock()
    fake_session.execute.return_value.all.return_value = [
        ("10101", "Caja General", 1000.0, 0.0),
        ("31001", "Capital Social", 0.0, 1000.0),
    ]

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=fake_session):
        client = TestClient(app)
        response = client.get(
            "/reportes/balance-comprobacion",
            params={"empresa_id": 11, "desde": "2026-08-01", "hasta": "2026-08-31"},
        )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    filas = response.json()
    assert filas[0]["numero_cta"] == "10101"
    assert filas[0]["saldo"] == 1000.0
    assert filas[1]["saldo"] == -1000.0
