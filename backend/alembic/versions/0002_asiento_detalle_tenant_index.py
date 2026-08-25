"""agrega indice (tenant_id, asiento_id) a asiento_detalle

Revision ID: 0002_asiento_detalle_tenant_index
Revises: 0001_initial_schema
Create Date: 2026-08-25

asiento_detalle es la tabla de mayor escritura del sistema y no tenia
ningun indice mas alla de la PK en id. Con RLS activo, cada consulta
filtrada por tenant_id hacia table scan completo (hallazgo de
plan-eng-review, ver docs/designs/nucleo-contabilidad-nomina.md).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002_asiento_tenant_idx"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_asiento_detalle_tenant_asiento",
        "asiento_detalle",
        ["tenant_id", "asiento_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_asiento_detalle_tenant_asiento", table_name="asiento_detalle")
