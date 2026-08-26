from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.lote_cosecha import LoteCosecha
from app.models.sucursal import Sucursal
from app.models.usuario import Usuario


def verificar_acceso_empresa(usuario: Usuario, empresa_id: int) -> None:
    """Un usuario con empresa_id fijo (rol restringido a una sola empresa)
    no puede leer ni escribir datos de otra empresa del mismo tenant.
    usuario.empresa_id is None significa acceso a todas las empresas del
    tenant (dueno/admin) -- ver app/models/usuario.py.
    """
    if usuario.empresa_id is not None and usuario.empresa_id != empresa_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a esta empresa")


def sucursales_de_empresa(empresa_id: int) -> Select:
    """Subquery de ids de sucursales de una empresa -- para filtrar tablas
    que no tienen empresa_id propio (Almacen, LoteCosecha) sin necesitar
    un JOIN explicito en cada endpoint.
    """
    return select(Sucursal.id).where(Sucursal.empresa_id == empresa_id)


def empresa_de_sucursal(db: Session, sucursal_id: int) -> int:
    """Resuelve la empresa dueña de una sucursal (o 404) -- para validar
    acceso en escrituras donde el payload solo trae sucursal_id, no
    empresa_id (Almacen, LoteCosecha).
    """
    sucursal = db.get(Sucursal, sucursal_id)
    if sucursal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sucursal no encontrada")
    return sucursal.empresa_id


def empresa_de_lote(db: Session, lote_id: int) -> int:
    """Resuelve la empresa dueña de un lote via su sucursal (o 404) --
    para validar acceso en inventario_movimientos, que solo trae lote_id.
    """
    lote = db.get(LoteCosecha, lote_id)
    if lote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote no encontrado")
    return empresa_de_sucursal(db, lote.sucursal_id)
