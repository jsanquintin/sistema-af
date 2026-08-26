import uuid
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.main import app
from app.models.regla_contabilizacion import ReglaContabilizacion
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


def test_listar_reglas_requiere_autenticacion():
    client = TestClient(app)
    response = client.get("/reglas-contabilizacion", params={"empresa_id": 1})
    assert response.status_code in (401, 403)


def test_crear_regla_fija_tenant_id():
    usuario = _fake_usuario()
    fake_session = MagicMock()
    fake_session.refresh.side_effect = lambda obj: setattr(obj, "id", 1)

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=fake_session):
        client = TestClient(app)
        response = client.post(
            "/reglas-contabilizacion",
            json={
                "empresa_id": 11,
                "origen_tipo": "nomina",
                "codigo_evento": "JORNALES_COSECHA",
                "numero_cta": "60101",
                "debcred": "D",
            },
        )
    app.dependency_overrides.clear()

    assert response.status_code == 201
    creada = fake_session.add.call_args[0][0]
    assert isinstance(creada, ReglaContabilizacion)
    assert creada.tenant_id == usuario.tenant_id
    assert creada.empresa_id == 11


def test_crear_regla_rechaza_empresa_no_autorizada():
    usuario = _fake_usuario(empresa_id=7)

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=MagicMock()):
        client = TestClient(app)
        response = client.post(
            "/reglas-contabilizacion",
            json={
                "empresa_id": 9,
                "origen_tipo": "nomina",
                "codigo_evento": "JORNALES_COSECHA",
                "numero_cta": "60101",
                "debcred": "D",
            },
        )
    app.dependency_overrides.clear()

    assert response.status_code == 403
