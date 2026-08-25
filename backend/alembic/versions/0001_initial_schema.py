"""versiona schema_agrocasa_creixa.sql como esquema inicial

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-08-24

Ejecuta tal cual el esquema ya validado contra Postgres 16 real (ver
CONTEXTO.md / backend/schema_agrocasa_creixa.sql) en vez de
reescribirlo como operaciones op.create_table(): ese archivo es la fuente
de verdad (24 tablas, RLS, trigger de cuadre) y duplicarlo aquí como
modelos ORM introduciría el riesgo de que las dos copias diverjan antes
de que exista una sola línea de lógica de negocio.

Se usa exec_driver_sql (no op.execute) para mandar el script completo tal
cual al driver, sin que SQLAlchemy intente interpretar los "::" de casteo
de Postgres ni ningún ":nombre" como bind param.
"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# backend/alembic/versions/0001_initial_schema.py -> versions -> alembic -> backend
SCHEMA_SQL_PATH = Path(__file__).resolve().parents[2] / "schema_agrocasa_creixa.sql"

_TABLES_EN_ORDEN_DE_CREACION = [
    "tenants",
    "empresas",
    "sucursales",
    "almacenes",
    "plan_cuentas",
    "asientos",
    "asiento_detalle",
    "reglas_contabilizacion",
    "empleados",
    "nomina_corridas",
    "nomina_detalle",
    "lotes_cosecha",
    "inventario_movimientos",
    "clientes",
    "facturas",
    "factura_detalle",
    "usuarios",
    "secuencias_ecf",
    "auditoria",
]


def upgrade() -> None:
    sql = SCHEMA_SQL_PATH.read_text(encoding="utf-8")
    # exec_driver_sql siempre manda un objeto de parametros (vacio) al driver,
    # y psycopg2 interpreta cualquier "%" suelto del texto como su propio
    # placeholder. El schema usa "%" legitimo de PL/pgSQL (RAISE EXCEPTION,
    # format('%I ...')) asi que se escapa como "%%" para que psycopg2 lo
    # revierta a "%" antes de mandarlo a Postgres.
    op.get_bind().exec_driver_sql(sql.replace("%", "%%"))


def downgrade() -> None:
    bind = op.get_bind()
    tablas = ", ".join(reversed(_TABLES_EN_ORDEN_DE_CREACION))
    bind.exec_driver_sql(f"DROP TABLE IF EXISTS {tablas} CASCADE")
    bind.exec_driver_sql("DROP FUNCTION IF EXISTS fn_validar_cuadre_asiento() CASCADE")
