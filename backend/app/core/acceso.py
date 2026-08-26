from fastapi import HTTPException, status

from app.models.usuario import Usuario


def verificar_acceso_empresa(usuario: Usuario, empresa_id: int) -> None:
    """Un usuario con empresa_id fijo (rol restringido a una sola empresa)
    no puede leer ni escribir datos de otra empresa del mismo tenant.
    usuario.empresa_id is None significa acceso a todas las empresas del
    tenant (dueno/admin) -- ver app/models/usuario.py.
    """
    if usuario.empresa_id is not None and usuario.empresa_id != empresa_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a esta empresa")
