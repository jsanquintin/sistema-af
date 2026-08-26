import uuid
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.main import app
from app.models.nomina import NominaCorrida
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


def test_listar_corridas_requiere_autenticacion():
    client = TestClient(app)
    response = client.get("/nomina-corridas", params={"empresa_id": 1})
    assert response.status_code in (401, 403)


def test_crear_corrida_fija_tenant_id_y_no_cerrada():
    usuario = _fake_usuario()
    fake_session = MagicMock()
    fake_session.refresh.side_effect = lambda obj: setattr(obj, "id", 1)

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=fake_session):
        client = TestClient(app)
        response = client.post(
            "/nomina-corridas",
            json={
                "empresa_id": 11,
                "codigo": "Q1",
                "nombre": "Nomina quincenal Ocoa",
                "periodo_inicio": "2026-08-01",
                "periodo_fin": "2026-08-15",
            },
        )
    app.dependency_overrides.clear()

    assert response.status_code == 201
    creada = fake_session.add.call_args[0][0]
    assert isinstance(creada, NominaCorrida)
    assert creada.tenant_id == usuario.tenant_id
    assert creada.cerrada is False


def test_crear_corrida_rechaza_empresa_no_autorizada():
    usuario = _fake_usuario(empresa_id=7)

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=MagicMock()):
        client = TestClient(app)
        response = client.post(
            "/nomina-corridas",
            json={
                "empresa_id": 9,
                "codigo": "Q1",
                "nombre": "Nomina quincenal Ocoa",
                "periodo_inicio": "2026-08-01",
                "periodo_fin": "2026-08-15",
            },
        )
    app.dependency_overrides.clear()

    assert response.status_code == 403


def test_cerrar_corrida_ya_cerrada_devuelve_409():
    usuario = _fake_usuario()
    corrida_cerrada = NominaCorrida(
        id=1,
        tenant_id=usuario.tenant_id,
        empresa_id=11,
        codigo="Q1",
        nombre="Nomina quincenal Ocoa",
        periodo_inicio="2026-08-01",
        periodo_fin="2026-08-15",
        cerrada=True,
    )
    fake_session = MagicMock()
    fake_session.get.return_value = corrida_cerrada

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=fake_session):
        client = TestClient(app)
        response = client.post("/nomina-corridas/1/cerrar")
    app.dependency_overrides.clear()

    assert response.status_code == 409
