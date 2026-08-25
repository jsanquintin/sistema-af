from fastapi import FastAPI

from app.api import auth, plan_cuentas

app = FastAPI(title="sistema-af")
app.include_router(auth.router)
app.include_router(plan_cuentas.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
