import uuid
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.main import app
from app.models.usuario import Usuario


def test_listar_parametros_requiere_autenticacion():
    client = TestClient(app)
    response = client.get("/parametros-nomina")
    assert response.status_code in (401, 403)


def test_listar_parametros_no_filtra_por_empresa():
    usuario = Usuario(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        empresa_id=11,
        email="contador@agrocasa.com",
        nombre_completo="Contador",
        hash_password="irrelevante-en-este-test",
        rol="contador",
        activo=True,
    )
    fake_session = MagicMock()
    fake_session.execute.return_value.scalars.return_value.all.return_value = []

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=fake_session):
        client = TestClient(app)
        response = client.get("/parametros-nomina")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == []
