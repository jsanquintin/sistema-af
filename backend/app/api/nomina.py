from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.acceso import verificar_acceso_empresa
from app.core.deps import get_current_user, get_tenant_db
from app.models.empleado import Empleado
from app.models.nomina import NominaCorrida, NominaDetalle
from app.models.parametro_nomina import ParametroNomina
from app.models.sucursal import Sucursal
from app.models.usuario import Usuario
from app.schemas.nomina import (
    CalcularNominaRequest,
    NominaCorridaCreate,
    NominaCorridaResponse,
    NominaDetalleResponse,
)
from app.services import nomina_calculo, nomina_eventos
from app.services.contabilizacion import generar_asiento_automatico

router = APIRouter(prefix="/nomina-corridas", tags=["nomina"])


def _obtener_parametros(db: Session, anio_fiscal: int) -> ParametroNomina:
    parametros = db.execute(
        select(ParametroNomina).where(ParametroNomina.anio_fiscal == anio_fiscal)
    ).scalar_one_or_none()
    if parametros is None:
        raise ValueError(
            f"No hay parametros_nomina para el anio fiscal {anio_fiscal} -- "
            "cargar tramos ISR y tasas TSS de ese anio antes de calcular"
        )
    return parametros


def _obtener_o_404(db: Session, corrida_id: int, usuario: Usuario) -> NominaCorrida:
    corrida = db.get(NominaCorrida, corrida_id)
    if corrida is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Corrida no encontrada")
    verificar_acceso_empresa(usuario, corrida.empresa_id)
    return corrida


@router.get("", response_model=list[NominaCorridaResponse])
def listar_corridas(
    empresa_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> list[NominaCorrida]:
    verificar_acceso_empresa(usuario, empresa_id)
    query = select(NominaCorrida).where(NominaCorrida.empresa_id == empresa_id)
    return list(db.execute(query).scalars().all())


@router.post("", response_model=NominaCorridaResponse, status_code=status.HTTP_201_CREATED)
def crear_corrida(
    payload: NominaCorridaCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> NominaCorrida:
    verificar_acceso_empresa(usuario, payload.empresa_id)
    corrida = NominaCorrida(**payload.model_dump(), tenant_id=usuario.tenant_id, cerrada=False)
    db.add(corrida)
    db.commit()
    db.refresh(corrida)
    return corrida


@router.get("/{corrida_id}/detalle", response_model=list[NominaDetalleResponse])
def ver_detalle(
    corrida_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> list[NominaDetalle]:
    _obtener_o_404(db, corrida_id, usuario)
    query = select(NominaDetalle).where(NominaDetalle.nomina_corrida_id == corrida_id)
    return list(db.execute(query).scalars().all())


@router.post("/{corrida_id}/calcular", response_model=list[NominaDetalleResponse])
def calcular_corrida(
    corrida_id: int,
    payload: CalcularNominaRequest,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> list[NominaDetalle]:
    corrida = _obtener_o_404(db, corrida_id, usuario)
    if corrida.cerrada:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La corrida ya esta cerrada")

    try:
        parametros = _obtener_parametros(db, corrida.periodo_inicio.year)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    query = select(Empleado).where(Empleado.empresa_id == corrida.empresa_id, Empleado.activo.is_(True))
    if corrida.sucursal_id is not None:
        query = query.where(Empleado.sucursal_id == corrida.sucursal_id)
    empleados = list(db.execute(query).scalars())

    # Recalculo idempotente: reemplaza el detalle existente en vez de
    # acumular filas duplicadas si "calcular" se llama mas de una vez.
    existentes = list(
        db.execute(select(NominaDetalle).where(NominaDetalle.nomina_corrida_id == corrida_id)).scalars()
    )
    for fila in existentes:
        db.delete(fila)
    db.flush()

    nuevas_filas = []
    for empleado in empleados:
        dias_unidades = payload.dias_por_empleado.get(empleado.id)
        try:
            resultado = nomina_calculo.calcular_linea(
                empleado,
                dias_unidades=dias_unidades,
                periodo_inicio=corrida.periodo_inicio,
                periodo_fin=corrida.periodo_fin,
                parametros=parametros,
            )
        except ValueError as exc:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        fila = NominaDetalle(
            tenant_id=usuario.tenant_id,
            nomina_corrida_id=corrida.id,
            empleado_id=empleado.id,
            sucursal_id=empleado.sucursal_id or corrida.sucursal_id,
            dias_unidades=dias_unidades,
            monto_bruto=resultado.monto_bruto,
            retencion_isr=resultado.retencion_isr,
            retencion_tss=resultado.retencion_tss_empleado,
            monto_neto=resultado.monto_neto,
        )
        db.add(fila)
        nuevas_filas.append(fila)

    db.commit()
    for fila in nuevas_filas:
        db.refresh(fila)
    return nuevas_filas


@router.post("/{corrida_id}/cerrar", response_model=NominaCorridaResponse)
def cerrar_corrida(
    corrida_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> NominaCorrida:
    corrida = _obtener_o_404(db, corrida_id, usuario)
    if corrida.cerrada:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La corrida ya esta cerrada")

    detalle = list(
        db.execute(select(NominaDetalle).where(NominaDetalle.nomina_corrida_id == corrida_id)).scalars()
    )
    if not detalle:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La corrida no tiene lineas calculadas -- correr /calcular primero",
        )

    try:
        parametros = _obtener_parametros(db, corrida.periodo_inicio.year)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    eventos = []
    for fila in detalle:
        empleado = db.get(Empleado, fila.empleado_id)
        sucursal_id = fila.sucursal_id or empleado.sucursal_id
        if empleado is None or sucursal_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede determinar la sucursal del empleado {fila.empleado_id} para contabilizar",
            )
        sucursal = db.get(Sucursal, sucursal_id)

        # Recalcula (misma funcion, mismos parametros y dias_unidades ya
        # guardados) solo para recuperar tss_patronal/infotep/riesgos, que
        # no se persisten en nomina_detalle (ver models/nomina.py).
        try:
            resultado = nomina_calculo.calcular_linea(
                empleado,
                dias_unidades=fila.dias_unidades,
                periodo_inicio=corrida.periodo_inicio,
                periodo_fin=corrida.periodo_fin,
                parametros=parametros,
            )
            eventos.extend(nomina_eventos.eventos_para_linea(empleado=empleado, sucursal=sucursal, resultado=resultado))
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    try:
        asiento = generar_asiento_automatico(
            db,
            tenant_id=usuario.tenant_id,
            empresa_id=corrida.empresa_id,
            origen_tipo="nomina",
            origen_id=corrida.id,
            fecha=corrida.periodo_fin,
            descripcion=f"Nomina {corrida.nombre} ({corrida.periodo_inicio} a {corrida.periodo_fin})",
            eventos=eventos,
        )
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    corrida.cerrada = True
    corrida.asiento_id = asiento.id
    db.commit()
    db.refresh(corrida)
    return corrida
