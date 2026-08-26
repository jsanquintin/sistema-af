from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.acceso import verificar_acceso_empresa
from app.core.deps import get_current_user, get_tenant_db
from app.models.asiento import Asiento, AsientoDetalle
from app.models.usuario import Usuario
from app.schemas.asiento import AsientoCreate, AsientoDetalleCreate, AsientoDetalleResponse, AsientoResponse
from app.services import contabilizacion

router = APIRouter(prefix="/asientos", tags=["asientos"])


def _con_lineas(db: Session, asiento: Asiento) -> AsientoResponse:
    # No hay relationship() de ORM entre Asiento y AsientoDetalle (el
    # codebase no usa relationships en ningun modelo todavia) -- se
    # consulta y compone a mano, igual que el resto de los endpoints.
    lineas = list(db.execute(select(AsientoDetalle).where(AsientoDetalle.asiento_id == asiento.id)).scalars())
    return AsientoResponse(
        id=asiento.id,
        empresa_id=asiento.empresa_id,
        fecha=asiento.fecha,
        origen_tipo=asiento.origen_tipo,
        origen_id=asiento.origen_id,
        descripcion=asiento.descripcion,
        creado_por=asiento.creado_por,
        creado_en=asiento.creado_en,
        estado=asiento.estado,
        lineas=[AsientoDetalleResponse.model_validate(l) for l in lineas],
    )


def _obtener_o_404(db: Session, asiento_id: int, usuario: Usuario) -> Asiento:
    asiento = db.get(Asiento, asiento_id)
    if asiento is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asiento no encontrado")
    verificar_acceso_empresa(usuario, asiento.empresa_id)
    return asiento


@router.get("", response_model=list[AsientoResponse])
def listar_asientos(
    empresa_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> list[AsientoResponse]:
    verificar_acceso_empresa(usuario, empresa_id)
    asientos = list(db.execute(select(Asiento).where(Asiento.empresa_id == empresa_id)).scalars())
    return [_con_lineas(db, a) for a in asientos]


@router.post("", response_model=AsientoResponse, status_code=status.HTTP_201_CREATED)
def crear_asiento(
    empresa_id: int,
    payload: AsientoCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> AsientoResponse:
    verificar_acceso_empresa(usuario, empresa_id)
    try:
        asiento = contabilizacion.crear_asiento_manual(
            db,
            tenant_id=usuario.tenant_id,
            empresa_id=empresa_id,
            fecha=payload.fecha,
            descripcion=payload.descripcion,
            lineas=[l.model_dump() for l in payload.lineas],
            creado_por=usuario.nombre_completo,
        )
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _con_lineas(db, asiento)


@router.post("/{asiento_id}/lineas", response_model=AsientoResponse, status_code=status.HTTP_201_CREATED)
def agregar_linea(
    asiento_id: int,
    payload: AsientoDetalleCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> AsientoResponse:
    asiento = _obtener_o_404(db, asiento_id, usuario)
    try:
        contabilizacion.agregar_linea(
            db,
            asiento=asiento,
            numero_cta=payload.numero_cta,
            sucursal_id=payload.sucursal_id,
            debcred=payload.debcred,
            monto=payload.monto,
        )
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _con_lineas(db, asiento)


@router.post("/{asiento_id}/postear", response_model=AsientoResponse)
def postear_asiento(
    asiento_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> AsientoResponse:
    asiento = _obtener_o_404(db, asiento_id, usuario)
    try:
        contabilizacion.postear_asiento(db, asiento)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _con_lineas(db, asiento)
