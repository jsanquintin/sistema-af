from pydantic import BaseModel


class BalanceComprobacionLinea(BaseModel):
    numero_cta: str
    nombre: str
    debe: float
    haber: float
    saldo: float
