from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator


class InventarioMovimientoCreate(BaseModel):
    lote_id: int
    tipo_movimiento: Literal["entrada", "salida", "ajuste", "merma", "traslado"]
    almacen_origen_id: int | None = None
    almacen_destino_id: int | None = None
    cantidad: float
    referencia_doc: str | None = None
    fecha: date

    @model_validator(mode="after")
    def _requiere_almacenes_segun_tipo(self) -> "InventarioMovimientoCreate":
        # 'ajuste'/'merma' no mueven inventario entre almacenes, no exigen ninguno.
        if self.tipo_movimiento in ("salida", "traslado") and self.almacen_origen_id is None:
            raise ValueError(f"almacen_origen_id es obligatorio para movimientos de tipo '{self.tipo_movimiento}'")
        if self.tipo_movimiento in ("entrada", "traslado") and self.almacen_destino_id is None:
            raise ValueError(f"almacen_destino_id es obligatorio para movimientos de tipo '{self.tipo_movimiento}'")
        return self


class InventarioMovimientoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lote_id: int
    tipo_movimiento: str
    almacen_origen_id: int | None
    almacen_destino_id: int | None
    cantidad: float
    referencia_doc: str | None
    fecha: date
