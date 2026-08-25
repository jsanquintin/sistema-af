from fastapi import FastAPI

from app.api import auth

app = FastAPI(title="sistema-af")
app.include_router(auth.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
