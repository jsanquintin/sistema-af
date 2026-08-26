from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_db
from app.models.parametro_nomina import ParametroNomina
from app.schemas.parametro_nomina import ParametroNominaResponse

router = APIRouter(prefix="/parametros-nomina", tags=["parametros-nomina"])


@router.get("", response_model=list[ParametroNominaResponse])
def listar_parametros(db: Session = Depends(get_tenant_db)) -> list[ParametroNomina]:
    # Sin filtro de empresa/tenant a proposito -- ver app/models/parametro_nomina.py,
    # son parametros regulatorios nacionales, no datos de un tenant especifico.
    return list(db.execute(select(ParametroNomina)).scalars().all())
