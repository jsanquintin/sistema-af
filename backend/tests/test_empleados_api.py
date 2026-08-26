import uuid
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.main import app
from app.models.empleado import Empleado
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


def test_listar_empleados_requiere_autenticacion():
    client = TestClient(app)
    response = client.get("/empleados")
    assert response.status_code in (401, 403)


def test_crear_empleado_fija_tenant_id():
    usuario = _fake_usuario()
    fake_app_session = MagicMock()
    # db.refresh() en la vida real asigna el id que Postgres genero al
    # insertar; el mock no inserta nada, asi que lo simulamos a mano --
    # si no, la respuesta falla su propia validacion (id requerido).
    fake_app_session.refresh.side_effect = lambda obj: setattr(obj, "id", 1)

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=fake_app_session):
        client = TestClient(app)
        response = client.post(
            "/empleados",
            json={
                "empresa_id": 11,
                "nombre_completo": "Juan Perez",
                "tipo_empleado": "jornalero",
                "incluye_tss": False,
            },
        )
    app.dependency_overrides.clear()

    assert response.status_code == 201
    creado = fake_app_session.add.call_args[0][0]
    assert isinstance(creado, Empleado)
    assert creado.tenant_id == usuario.tenant_id
    assert creado.empresa_id == 11


def test_crear_empleado_rechaza_empresa_no_autorizada():
    usuario = _fake_usuario(empresa_id=7)

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=MagicMock()):
        client = TestClient(app)
        response = client.post(
            "/empleados",
            json={"empresa_id": 9, "nombre_completo": "Juan Perez", "tipo_empleado": "fijo"},
        )
    app.dependency_overrides.clear()

    assert response.status_code == 403


def test_crear_empleado_rechaza_tipo_empleado_invalido():
    usuario = _fake_usuario()

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=MagicMock()):
        client = TestClient(app)
        response = client.post(
            "/empleados",
            json={"empresa_id": 11, "nombre_completo": "Juan Perez", "tipo_empleado": "gerente"},
        )
    app.dependency_overrides.clear()

    assert response.status_code == 422
