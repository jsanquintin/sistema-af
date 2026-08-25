from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, plan_cuentas
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
app.include_router(plan_cuentas.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
