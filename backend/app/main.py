from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    almacenes,
    asientos,
    auth,
    clientes,
    empleados,
    empresas,
    facturas,
    inventario_movimientos,
    lotes_cosecha,
    nomina,
    obras,
    parametros_nomina,
    plan_cuentas,
    reglas_contabilizacion,
    reportes,
    superadmin,
    usuarios,
)
from app.core.config import settings

app = FastAPI(title="sistema-af")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(empresas.router)
app.include_router(plan_cuentas.router)
app.include_router(empleados.router)
app.include_router(clientes.router)
app.include_router(almacenes.router)
app.include_router(lotes_cosecha.router)
app.include_router(obras.router)
app.include_router(inventario_movimientos.router)
app.include_router(asientos.router)
app.include_router(reglas_contabilizacion.router)
app.include_router(nomina.router)
app.include_router(facturas.router)
app.include_router(reportes.router)
app.include_router(parametros_nomina.router)
app.include_router(usuarios.router)
app.include_router(superadmin.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
