"""Motor de asientos: creacion manual, posteo, y generacion automatica
desde reglas_contabilizacion (diagrama en
docs/designs/nucleo-contabilidad-nomina.md).

El cuadre (debe=haber) ya no lo valida el trigger de Postgres para
asientos en borrador (ver alembic 0003_asientos_estado_empresa) -- se
valida aqui, antes de marcar un asiento como 'posteado', y se levanta
ValueError si no cuadra en vez de confiar en que las reglas de
contabilizacion siempre produzcan lineas balanceadas por si solas (si
alguien borra o desconfigura una regla, esto lo atrapa antes de escribir
un asiento posteado descuadrado).
"""
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asiento import Asiento, AsientoDetalle
from app.models.regla_contabilizacion import ReglaContabilizacion
from app.models.sucursal import Sucursal


@dataclass
class LineaEvento:
    codigo_evento: str
    monto: float
    sucursal_id: int | None = None


def validar_sucursal_pertenece_a_empresa(db: Session, sucursal_id: int, empresa_id: int) -> None:
    sucursal = db.get(Sucursal, sucursal_id)
    if sucursal is None or sucursal.empresa_id != empresa_id:
        raise ValueError(f"La sucursal {sucursal_id} no pertenece a la empresa {empresa_id}")


def _sumar_por_lado(lineas: Sequence[AsientoDetalle]) -> tuple[float, float]:
    debe = sum(float(l.monto) for l in lineas if l.debcred == "D")
    haber = sum(float(l.monto) for l in lineas if l.debcred == "C")
    return debe, haber


def crear_asiento_manual(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    empresa_id: int,
    fecha: date,
    descripcion: str | None,
    lineas: Sequence[dict],
    creado_por: str | None,
) -> Asiento:
    for linea in lineas:
        if linea.get("sucursal_id") is not None:
            validar_sucursal_pertenece_a_empresa(db, linea["sucursal_id"], empresa_id)

    asiento = Asiento(
        tenant_id=tenant_id,
        empresa_id=empresa_id,
        fecha=fecha,
        origen_tipo="manual",
        descripcion=descripcion,
        creado_por=creado_por,
        estado="borrador",
    )
    db.add(asiento)
    db.flush()  # necesita asiento.id para insertar las lineas

    for linea in lineas:
        db.add(
            AsientoDetalle(
                tenant_id=tenant_id,
                asiento_id=asiento.id,
                empresa_id=empresa_id,
                numero_cta=linea["numero_cta"],
                sucursal_id=linea.get("sucursal_id"),
                debcred=linea["debcred"],
                monto=linea["monto"],
            )
        )
    db.commit()
    db.refresh(asiento)
    return asiento


def agregar_linea(
    db: Session, *, asiento: Asiento, numero_cta: str, sucursal_id: int | None, debcred: str, monto: float
) -> AsientoDetalle:
    if asiento.estado == "posteado":
        raise ValueError(f"Asiento {asiento.id} ya esta posteado -- es inmutable")
    if sucursal_id is not None:
        validar_sucursal_pertenece_a_empresa(db, sucursal_id, asiento.empresa_id)

    linea = AsientoDetalle(
        tenant_id=asiento.tenant_id,
        asiento_id=asiento.id,
        empresa_id=asiento.empresa_id,
        numero_cta=numero_cta,
        sucursal_id=sucursal_id,
        debcred=debcred,
        monto=monto,
    )
    db.add(linea)
    db.commit()
    db.refresh(linea)
    return linea


def postear_asiento(db: Session, asiento: Asiento) -> Asiento:
    if asiento.estado == "posteado":
        raise ValueError(f"Asiento {asiento.id} ya esta posteado")

    lineas = list(db.execute(select(AsientoDetalle).where(AsientoDetalle.asiento_id == asiento.id)).scalars())
    if not lineas:
        raise ValueError(f"Asiento {asiento.id} no tiene lineas, no se puede postear")

    debe, haber = _sumar_por_lado(lineas)
    if debe != haber:
        raise ValueError(f"Asiento {asiento.id} descuadrado: debe={debe} haber={haber}")

    asiento.estado = "posteado"
    db.commit()
    db.refresh(asiento)
    return asiento


def generar_asiento_automatico(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    empresa_id: int,
    origen_tipo: str,
    origen_id: int,
    fecha: date,
    descripcion: str | None,
    eventos: Sequence[LineaEvento],
) -> Asiento:
    if not eventos:
        raise ValueError("No hay eventos para generar el asiento")

    # Batch-fetch: una sola query para todas las reglas del origen, evita
    # N+1 (issue #4 de plan-eng-review sobre el design doc).
    reglas = list(
        db.execute(
            select(ReglaContabilizacion).where(
                ReglaContabilizacion.tenant_id == tenant_id,
                ReglaContabilizacion.empresa_id == empresa_id,
                ReglaContabilizacion.origen_tipo == origen_tipo,
            )
        ).scalars()
    )
    reglas_por_evento: dict[str, list[ReglaContabilizacion]] = {}
    for regla in reglas:
        reglas_por_evento.setdefault(regla.codigo_evento, []).append(regla)

    codigos_faltantes = {e.codigo_evento for e in eventos} - reglas_por_evento.keys()
    if codigos_faltantes:
        # Falla ANTES de abrir la transaccion de escritura -- no dejar que
        # trg_cuadre_asiento (o el chequeo de abajo) lo atrape tarde.
        raise ValueError(
            f"Sin regla de contabilizacion para: {', '.join(sorted(codigos_faltantes))} "
            f"(empresa {empresa_id}, origen {origen_tipo})"
        )

    for evento in eventos:
        if evento.sucursal_id is not None:
            validar_sucursal_pertenece_a_empresa(db, evento.sucursal_id, empresa_id)

    asiento = Asiento(
        tenant_id=tenant_id,
        empresa_id=empresa_id,
        fecha=fecha,
        origen_tipo=origen_tipo,
        origen_id=origen_id,
        descripcion=descripcion,
        estado="borrador",
    )
    db.add(asiento)
    db.flush()

    detalles = []
    for evento in eventos:
        for regla in reglas_por_evento[evento.codigo_evento]:
            linea = AsientoDetalle(
                tenant_id=tenant_id,
                asiento_id=asiento.id,
                empresa_id=empresa_id,
                numero_cta=regla.numero_cta,
                sucursal_id=evento.sucursal_id,
                debcred=regla.debcred,
                monto=evento.monto,
            )
            db.add(linea)
            detalles.append(linea)

    # No se asume "balanceado por construccion" sin verificar: si
    # reglas_contabilizacion esta mal configurado (regla borrada/incompleta),
    # esto lo atrapa aqui. No se hace rollback en este punto -- el llamador
    # (capa de API) es quien decide el alcance de la transaccion y hace
    # rollback sobre cualquier ValueError, ya que puede haber otras filas
    # (factura, movimiento de inventario) pendientes en la misma sesion.
    debe, haber = _sumar_por_lado(detalles)
    if debe != haber:
        raise ValueError(
            f"Reglas de contabilizacion para origen={origen_tipo} producen un asiento descuadrado "
            f"(debe={debe} haber={haber}) -- revisar reglas_contabilizacion para empresa {empresa_id}"
        )

    asiento.estado = "posteado"
    db.commit()
    db.refresh(asiento)
    return asiento
