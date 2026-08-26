import uuid
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.main import app
from app.models.empresa import Empresa
from app.models.sucursal import Sucursal
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


def test_listar_empresas_fija_tenant_antes_de_consultar():
    usuario = _fake_usuario()
    empresa = Empresa(
        id=1,
        tenant_id=usuario.tenant_id,
        rnc="101-12843-7",
        razon_social="Agrotecnica Cafetera SRL",
        nombre_comercial="Agrocasa",
        activo=True,
    )

    fake_app_session = MagicMock()
    fake_app_session.execute.return_value.scalars.return_value.all.return_value = [empresa]

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=fake_app_session):
        client = TestClient(app)
        response = client.get("/empresas")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "rnc": "101-12843-7", "razon_social": "Agrotecnica Cafetera SRL", "nombre_comercial": "Agrocasa"}
    ]

    primera_llamada = fake_app_session.execute.call_args_list[0]
    assert "set_config" in str(primera_llamada.args[0])


def test_listar_empresas_requiere_autenticacion():
    client = TestClient(app)
    response = client.get("/empresas")
    assert response.status_code in (401, 403)


def test_listar_empresas_filtra_por_empresa_fija_del_usuario():
    # empresa_id no-NULL en el usuario restringe la consulta a esa empresa,
    # sin depender solo de lo que el frontend decida pedir.
    usuario = _fake_usuario(empresa_id=7)

    fake_app_session = MagicMock()
    fake_app_session.execute.return_value.scalars.return_value.all.return_value = []

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=fake_app_session):
        client = TestClient(app)
        client.get("/empresas")
    app.dependency_overrides.clear()

    segunda_llamada = fake_app_session.execute.call_args_list[1]
    assert "empresas.id" in str(segunda_llamada.args[0])


def test_listar_sucursales_rechaza_empresa_no_autorizada():
    usuario = _fake_usuario(empresa_id=7)

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=MagicMock()):
        client = TestClient(app)
        response = client.get("/empresas/9/sucursales")
    app.dependency_overrides.clear()

    assert response.status_code == 403


def test_listar_sucursales_de_empresa_autorizada():
    usuario = _fake_usuario(empresa_id=7)
    sucursal = Sucursal(
        id=1,
        tenant_id=usuario.tenant_id,
        empresa_id=7,
        codigo="OCOA",
        nombre="Ocoa",
        tipo="finca",
        activo=True,
    )

    fake_app_session = MagicMock()
    fake_app_session.execute.return_value.scalars.return_value.all.return_value = [sucursal]

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=fake_app_session):
        client = TestClient(app)
        response = client.get("/empresas/7/sucursales")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [{"id": 1, "empresa_id": 7, "codigo": "OCOA", "nombre": "Ocoa", "tipo": "finca"}]


def test_listar_sucursales_requiere_autenticacion():
    client = TestClient(app)
    response = client.get("/empresas/1/sucursales")
    assert response.status_code in (401, 403)


def test_crear_sucursal_fija_tenant_y_empresa():
    usuario = _fake_usuario()
    empresa = Empresa(id=7, tenant_id=usuario.tenant_id, rnc="131-71466-8", razon_social="Inversiones Creixa SRL")
    fake_app_session = MagicMock()
    fake_app_session.get.return_value = empresa
    fake_app_session.refresh.side_effect = lambda obj: setattr(obj, "id", 1)

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=fake_app_session):
        client = TestClient(app)
        response = client.post(
            "/empresas/7/sucursales",
            json={"codigo": "SD", "nombre": "Santo Domingo", "tipo": "oficina"},
        )
    app.dependency_overrides.clear()

    assert response.status_code == 201
    creada = fake_app_session.add.call_args[0][0]
    assert isinstance(creada, Sucursal)
    assert creada.tenant_id == usuario.tenant_id
    assert creada.empresa_id == 7
    assert creada.activo is True


def test_crear_sucursal_rechaza_empresa_no_autorizada():
    usuario = _fake_usuario(empresa_id=7)

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=MagicMock()):
        client = TestClient(app)
        response = client.post(
            "/empresas/9/sucursales",
            json={"codigo": "SD", "nombre": "Santo Domingo", "tipo": "oficina"},
        )
    app.dependency_overrides.clear()

    assert response.status_code == 403


def test_crear_sucursal_empresa_inexistente_devuelve_404():
    usuario = _fake_usuario()
    fake_app_session = MagicMock()
    fake_app_session.get.return_value = None

    app.dependency_overrides[get_current_user] = lambda: usuario
    with patch("app.core.deps.AppSessionLocal", return_value=fake_app_session):
        client = TestClient(app)
        response = client.post(
            "/empresas/99/sucursales",
            json={"codigo": "SD", "nombre": "Santo Domingo", "tipo": "oficina"},
        )
    app.dependency_overrides.clear()

    assert response.status_code == 404
