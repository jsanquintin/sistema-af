"""Panel de superadmin: alta/administracion de tenants.

Control plane separado a proposito de `usuarios.py` -- ver
docs/designs/panel-superadmin-multitenant.md. `superadmins` no tiene
tenant_id ni RLS; un JWT de superadmin nunca puede usarse contra un
endpoint tenant-scoped porque get_current_user exige tenant_id y falla
cerrado si falta.

El login de superadmin NO vive aca -- comparte formulario y endpoint con
el login de tenant (`POST /auth/login`, ver app/api/auth.py) para que el
usuario no necesite conocer una URL separada; ese endpoint prueba
`usuarios` primero y `superadmins` despues.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.deps import get_current_superadmin, get_superadmin_db
from app.core.security import create_access_token, hash_password
from app.models.superadmin import Superadmin
from app.models.superadmin_auditoria import SuperadminAuditoria
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.schemas.auth import TokenResponse
from app.schemas.superadmin import (
    TenantCreateRequest,
    TenantCreateResponse,
    TenantResponse,
    TenantUpdateRequest,
)

router = APIRouter(prefix="/superadmin", tags=["superadmin"])


def _set_tenant_context(db: Session, tenant_id: uuid.UUID) -> None:
    db.execute(text("SELECT set_config('app.tenant_id', :tenant_id, true)"), {"tenant_id": str(tenant_id)})


def _log(db: Session, superadmin: Superadmin, tenant_id: uuid.UUID, accion: str, detalle: dict | None = None) -> None:
    db.add(SuperadminAuditoria(superadmin_id=superadmin.id, tenant_id=tenant_id, accion=accion, detalle=detalle))


@router.get("/tenants", response_model=list[TenantResponse])
def listar_tenants(
    superadmin: Superadmin = Depends(get_current_superadmin),
    db: Session = Depends(get_superadmin_db),
) -> list[Tenant]:
    return list(db.execute(select(Tenant).order_by(Tenant.nombre)).scalars().all())


@router.post("/tenants", response_model=TenantCreateResponse, status_code=status.HTTP_201_CREATED)
def crear_tenant(
    payload: TenantCreateRequest,
    superadmin: Superadmin = Depends(get_current_superadmin),
    db: Session = Depends(get_superadmin_db),
) -> TenantCreateResponse:
    tenant = Tenant(id=uuid.uuid4(), nombre=payload.nombre, activo=True)
    db.add(tenant)
    db.flush()

    # A partir de aca el tenant ya existe: fijar el contexto a ESE tenant
    # (nunca antes) es lo que permite que el INSERT de abajo pase la
    # politica RLS de `usuarios` sin necesitar un rol con BYPASSRLS.
    _set_tenant_context(db, tenant.id)

    usuario = Usuario(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        empresa_id=None,
        email=payload.admin_email,
        nombre_completo=payload.admin_nombre_completo,
        hash_password=hash_password(payload.admin_password),
        rol="admin",
        activo=True,
    )
    db.add(usuario)

    _log(db, superadmin, tenant.id, "crear_tenant", {"admin_email": payload.admin_email})

    # Se arma la respuesta ANTES del commit: expire_on_commit reexpira los
    # atributos ORM despues de COMMIT, y una relectura de `usuarios` fuera
    # de esta transaccion ya no tendria app.tenant_id fijado (SET LOCAL es
    # por-transaccion).
    respuesta = TenantCreateResponse(
        tenant=TenantResponse(id=tenant.id, nombre=tenant.nombre, activo=tenant.activo),
        admin_email=usuario.email,
    )
    db.commit()
    return respuesta


@router.patch("/tenants/{tenant_id}", response_model=TenantResponse)
def actualizar_tenant(
    tenant_id: uuid.UUID,
    payload: TenantUpdateRequest,
    superadmin: Superadmin = Depends(get_current_superadmin),
    db: Session = Depends(get_superadmin_db),
) -> Tenant:
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")

    tenant.activo = payload.activo
    _log(db, superadmin, tenant.id, "activar_tenant" if payload.activo else "desactivar_tenant")
    db.commit()
    return tenant


@router.post("/tenants/{tenant_id}/entrar", response_model=TokenResponse)
def entrar_a_tenant(
    tenant_id: uuid.UUID,
    superadmin: Superadmin = Depends(get_current_superadmin),
    db: Session = Depends(get_superadmin_db),
) -> TokenResponse:
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")

    _set_tenant_context(db, tenant.id)
    admin = db.execute(
        select(Usuario)
        .where(Usuario.tenant_id == tenant.id, Usuario.rol == "admin", Usuario.activo.is_(True))
        .order_by(Usuario.creado_en.asc())
        .limit(1)
    ).scalar_one_or_none()

    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="El tenant no tiene ningun administrador activo"
        )

    _log(db, superadmin, tenant.id, "impersonar", {"usuario_id": str(admin.id)})

    # Igual que en crear_tenant: el token se arma con los valores ya en
    # memoria, antes del commit que termina la transaccion (y con ella el
    # SET LOCAL de app.tenant_id).
    token = create_access_token(usuario_id=admin.id, tenant_id=tenant.id, rol=admin.rol, impersonated_by=superadmin.id)
    db.commit()
    return TokenResponse(access_token=token)
