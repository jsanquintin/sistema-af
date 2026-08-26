import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.main import app
from app.models.asiento import Asiento
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


def _refresh(obj):
    # db.refresh() en la vida real recarga columnas con server_default
    # (creado_en) ademas del id -- el mock no inserta nada de verdad, asi
    # que se simula a mano para que la respuesta pase su propia validacion.
    obj.id = 1
    if hasattr(obj, "creado_en") and obj.creado_en is None:
        obj.creado_en = datetime(2026, 8, 26, 12, 0, 0)


def _fake_session_para_crear():
    session = MagicMock()
    session.refresh.side_effect = _refresh
    # _con_lineas hace un SELECT extra despues de crear -- sin filas reales
    # de vuelta (sesion mockeada), se configura vacio a proposito.
    session.execute.return_value.scalars.return_value = []
    return session


def test_listar_asientos_requiere_autenticacion():
    client = TestClient(app)
    response = client.get("/asientos", params={"empresa_id": 1})
    assert response.status_code in (401, 403)


def test_crear_asiento_manual_en_borrador():
    usuario = _fake_usuario()
    fake_session = _fake_session_para_crear()

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=fake_session):
        client = TestClient(app)
        response = client.post(
            "/asientos",
            params={"empresa_id": 11},
            json={
                "fecha": "2026-08-26",
                "descripcion": "Apertura de caja",
                "lineas": [
                    {"numero_cta": "10101", "debcred": "D", "monto": 1000},
                    {"numero_cta": "31001", "debcred": "C", "monto": 1000},
                ],
            },
        )
    app.dependency_overrides.clear()

    assert response.status_code == 201
    asientos_creados = [c.args[0] for c in fake_session.add.call_args_list if isinstance(c.args[0], Asiento)]
    assert len(asientos_creados) == 1
    assert asientos_creados[0].estado == "borrador"
    assert asientos_creados[0].origen_tipo == "manual"
    assert asientos_creados[0].empresa_id == 11


def test_crear_asiento_rechaza_empresa_no_autorizada():
    usuario = _fake_usuario(empresa_id=7)

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=MagicMock()):
        client = TestClient(app)
        response = client.post(
            "/asientos",
            params={"empresa_id": 9},
            json={"fecha": "2026-08-26", "lineas": [{"numero_cta": "10101", "debcred": "D", "monto": 1}]},
        )
    app.dependency_overrides.clear()

    assert response.status_code == 403


def test_crear_asiento_rechaza_sin_lineas():
    usuario = _fake_usuario()

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=MagicMock()):
        client = TestClient(app)
        response = client.post("/asientos", params={"empresa_id": 11}, json={"fecha": "2026-08-26", "lineas": []})
    app.dependency_overrides.clear()

    assert response.status_code == 422
