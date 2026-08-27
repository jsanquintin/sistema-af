"""tablas superadmins y superadmin_auditoria (panel de superadmin multi-tenant)

Revision ID: 0006_superadmin_panel
Revises: 0005_obras_costeo_proyecto
Create Date: 2026-08-27

Contexto (docs/designs/panel-superadmin-multitenant.md): un segundo
tenant real esta por darse de alta, lo que dispara el trabajo de
"endurecer multi-tenant" que nucleo-contabilidad-nomina.md habia
diferido a proposito. Al revisar el schema se confirmo que NO hace
falta el rol Postgres con BYPASSRLS que CONTEXTO.md habia anticipado:
`tenants` ya vive fuera del boundary de RLS (no tiene tenant_id), y
estas dos tablas nuevas se agregan deliberadamente SIN RLS por el mismo
motivo -- son el control plane, no datos de un tenant. El unico INSERT
que si toca una tabla con RLS (el primer `usuario` de un tenant nuevo)
se resuelve fijando app.tenant_id al tenant recien creado antes de
insertar, dentro de la misma transaccion (ver app/api/superadmin.py).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0006_superadmin_panel"
down_revision: Union[str, None] = "0005_obras_costeo_proyecto"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    def run(sql: str) -> None:
        bind.exec_driver_sql(sql)

    run(
        """
        CREATE TABLE superadmins (
            id              UUID PRIMARY KEY,
            email           VARCHAR(150) NOT NULL UNIQUE,
            nombre_completo VARCHAR(150) NOT NULL,
            hash_password   VARCHAR(200) NOT NULL,
            activo          BOOLEAN NOT NULL DEFAULT TRUE,
            creado_en       TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    run(
        """
        CREATE TABLE superadmin_auditoria (
            id              BIGSERIAL PRIMARY KEY,
            superadmin_id   UUID NOT NULL REFERENCES superadmins(id),
            tenant_id       UUID NOT NULL REFERENCES tenants(id),
            accion          VARCHAR(50) NOT NULL,
            detalle         JSONB,
            creado_en       TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    run("CREATE INDEX ix_superadmin_auditoria_tenant ON superadmin_auditoria (tenant_id)")

    # Deliberadamente SIN ENABLE/FORCE ROW LEVEL SECURITY: estas tablas son
    # el control plane (superadmins administrando tenants), no datos que
    # pertenezcan a un tenant. Ver docstring de este archivo.


def downgrade() -> None:
    bind = op.get_bind()
    bind.exec_driver_sql("DROP TABLE IF EXISTS superadmin_auditoria CASCADE")
    bind.exec_driver_sql("DROP TABLE IF EXISTS superadmins CASCADE")
