"""tabla obras (costeo de proyecto de construccion) + costeable en
nomina_corridas y facturas

Revision ID: 0005_obras_costeo_proyecto
Revises: 0004_parametros_nomina
Create Date: 2026-08-26

Contexto (docs/designs/nucleo-contabilidad-nomina.md, seccion
"Integracion diferida"): al verificar el RNC real de Creixa en DGII se
confirmo que es una constructora, no una empresa de inversion. Un lote
de cosecha (Agrocasa) se vende entero en una factura; un proyecto de
construccion (Creixa) se factura por avances a lo largo del tiempo, asi
que no puede reusar el mismo mecanismo de "reconocer todo el costo
acumulado en la primera factura" -- de ahi costo_reconocido, separado de
costo_acumulado, para reconocer solo el delta en cada factura contra la
obra.

nomina_corridas.costeable_tipo/costeable_id (sin FK real, mismo patron
polimorfico que asientos.origen_id en el schema original) permite
asignar una corrida completa a un lote o una obra -- el costo de mano de
obra de esa corrida se suma al costo_acumulado del costeable al cerrar
la corrida (backend/app/api/nomina.py::cerrar_corrida). No hay
prorrateo por linea/empleado: si hace falta dividir el costo de una
corrida entre varios lotes/obras, se corren corridas separadas.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0005_obras_costeo_proyecto"
down_revision: Union[str, None] = "0004_parametros_nomina"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    def run(sql: str) -> None:
        bind.exec_driver_sql(sql.replace("%", "%%"))

    run(
        """
        CREATE TABLE obras (
            id                  SERIAL PRIMARY KEY,
            tenant_id           UUID NOT NULL REFERENCES tenants(id),
            empresa_id          INTEGER NOT NULL REFERENCES empresas(id),
            sucursal_id         INTEGER NOT NULL UNIQUE REFERENCES sucursales(id),
            cliente_id          INTEGER NOT NULL REFERENCES clientes(id),
            codigo              VARCHAR(20) NOT NULL,
            nombre              VARCHAR(150) NOT NULL,
            monto_contrato      NUMERIC(14,2) NOT NULL,
            moneda              VARCHAR(3) NOT NULL DEFAULT 'DOP',
            fecha_inicio        DATE NOT NULL,
            fecha_fin_estimada  DATE,
            costo_acumulado     NUMERIC(14,2) NOT NULL DEFAULT 0,
            costo_reconocido    NUMERIC(14,2) NOT NULL DEFAULT 0,
            estado              VARCHAR(20) NOT NULL DEFAULT 'en_proceso'
                                    CHECK (estado IN ('en_proceso','cerrada')),
            CHECK (costo_reconocido <= costo_acumulado),
            UNIQUE (tenant_id, codigo)
        )
        """
    )
    run("CREATE INDEX ix_obras_tenant_empresa ON obras (tenant_id, empresa_id)")

    # RLS: obras nace fuera de schema_agrocasa_creixa.sql, asi que no
    # hereda el DO $$ ... $$ que fuerza RLS en las tablas originales --
    # hay que repetirlo aqui explicitamente, tabla por tabla.
    run("ALTER TABLE obras ENABLE ROW LEVEL SECURITY")
    run("ALTER TABLE obras FORCE ROW LEVEL SECURITY")
    run(
        """
        CREATE POLICY tenant_isolation ON obras
            USING (tenant_id = current_setting('app.tenant_id')::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid)
        """
    )

    run("ALTER TABLE facturas ADD COLUMN obra_id INTEGER REFERENCES obras(id)")
    run(
        "ALTER TABLE facturas ADD CONSTRAINT facturas_lote_o_obra_check "
        "CHECK (NOT (lote_id IS NOT NULL AND obra_id IS NOT NULL))"
    )

    run(
        "ALTER TABLE nomina_corridas ADD COLUMN costeable_tipo VARCHAR(10) "
        "CHECK (costeable_tipo IN ('lote','obra'))"
    )
    run("ALTER TABLE nomina_corridas ADD COLUMN costeable_id INTEGER")
    run(
        "ALTER TABLE nomina_corridas ADD CONSTRAINT nomina_corridas_costeable_check "
        "CHECK ((costeable_tipo IS NULL) = (costeable_id IS NULL))"
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.exec_driver_sql("ALTER TABLE nomina_corridas DROP CONSTRAINT nomina_corridas_costeable_check")
    bind.exec_driver_sql("ALTER TABLE nomina_corridas DROP COLUMN costeable_id")
    bind.exec_driver_sql("ALTER TABLE nomina_corridas DROP COLUMN costeable_tipo")
    bind.exec_driver_sql("ALTER TABLE facturas DROP CONSTRAINT facturas_lote_o_obra_check")
    bind.exec_driver_sql("ALTER TABLE facturas DROP COLUMN obra_id")
    bind.exec_driver_sql("DROP TABLE IF EXISTS obras CASCADE")
