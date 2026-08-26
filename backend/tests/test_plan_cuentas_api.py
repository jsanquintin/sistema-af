import uuid
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.main import app
from app.models.plan_cuenta import PlanCuenta
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


def test_listar_plan_cuentas_fija_tenant_antes_de_consultar():
    usuario = _fake_usuario()
    cuenta = PlanCuenta(
        id=1,
        tenant_id=usuario.tenant_id,
        empresa_id=11,
        numero_cta="10000000",
        nivel=1,
        tipo_cta=1,
        nombre="Activos",
        activo=True,
    )

    fake_app_session = MagicMock()
    fake_app_session.execute.return_value.scalars.return_value.all.return_value = [cuenta]

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=fake_app_session):
        client = TestClient(app)
        response = client.get("/plan-cuentas", params={"empresa_id": 11})
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "empresa_id": 11,
            "numero_cta": "10000000",
            "nivel": 1,
            "tipo_cta": 1,
            "nombre": "Activos",
            "activo": True,
        }
    ]

    # La primera llamada a execute debe ser el set_config del tenant --
    # antes de cualquier consulta de negocio, no despues.
    primera_llamada = fake_app_session.execute.call_args_list[0]
    sql_text = str(primera_llamada.args[0])
    params = primera_llamada.args[1]
    assert "set_config" in sql_text
    assert params == {"tenant_id": str(usuario.tenant_id)}


def test_listar_plan_cuentas_requiere_autenticacion():
    client = TestClient(app)
    response = client.get("/plan-cuentas")
    assert response.status_code in (401, 403)
