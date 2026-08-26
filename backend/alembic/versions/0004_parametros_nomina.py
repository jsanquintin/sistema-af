"""tabla parametros_nomina (tramos ISR + tasas TSS por ano fiscal)

Revision ID: 0004_parametros_nomina
Revises: 0003_asientos_estado_empresa
Create Date: 2026-08-26

Open Question 6 (docs/designs/nucleo-contabilidad-nomina.md): las tasas y
topes de ISR/TSS no se hardcodean en el motor de calculo porque DGII/TSS
las ajusta por decreto (los umbrales de ISR se indexan por inflacion cada
ano). Se versiona por anio_fiscal en vez de en codigo.

Deliberadamente SIN tenant_id y SIN RLS: a diferencia del resto del
schema, ISR y TSS son parametros regulatorios nacionales (DGII/TSS) que
aplican igual a todos los tenants -- no es un dato de negocio de un
cliente especifico, es una tabla de referencia compartida, igual que un
catalogo de codigos postales seria. Por eso tampoco se agrega a la lista
de tablas con FORCE ROW LEVEL SECURITY del schema original.

La fila sembrada para 2026 usa la ESTRUCTURA real de la retencion sobre
asalariados (4 tramos, metodo de anualizacion 360 dias) con montos de
umbral representativos del rango vigente reciente -- ver la columna
`notas`: estos montos y el salario minimo de referencia deben verificarse
contra la tabla DGII/TSS vigente antes de usarse para nomina real, no son
una consulta directa al portal de DGII.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0004_parametros_nomina"
down_revision: Union[str, None] = "0003_asientos_estado_empresa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    bind.exec_driver_sql(
        """
        CREATE TABLE parametros_nomina (
            id                              SERIAL PRIMARY KEY,
            anio_fiscal                     SMALLINT NOT NULL UNIQUE,
            isr_tramo1_hasta                NUMERIC(14,2) NOT NULL,
            isr_tramo2_hasta                NUMERIC(14,2) NOT NULL,
            isr_tramo3_hasta                NUMERIC(14,2) NOT NULL,
            isr_tramo2_tasa                 NUMERIC(5,2) NOT NULL DEFAULT 15,
            isr_tramo3_tasa                 NUMERIC(5,2) NOT NULL DEFAULT 20,
            isr_tramo4_tasa                 NUMERIC(5,2) NOT NULL DEFAULT 25,
            tss_sfs_empleado_pct            NUMERIC(5,2) NOT NULL DEFAULT 3.04,
            tss_sfs_patronal_pct            NUMERIC(5,2) NOT NULL DEFAULT 7.09,
            tss_afp_empleado_pct            NUMERIC(5,2) NOT NULL DEFAULT 2.87,
            tss_afp_patronal_pct            NUMERIC(5,2) NOT NULL DEFAULT 7.10,
            tss_riesgos_laborales_pct       NUMERIC(5,2) NOT NULL DEFAULT 1.20,
            tss_infotep_pct                 NUMERIC(5,2) NOT NULL DEFAULT 1.00,
            tss_tope_sfs_salarios_minimos   SMALLINT NOT NULL DEFAULT 10,
            tss_tope_afp_salarios_minimos   SMALLINT NOT NULL DEFAULT 20,
            salario_minimo_referencia       NUMERIC(14,2) NOT NULL,
            notas                           VARCHAR(300)
        )
        """
    )
    bind.exec_driver_sql(
        """
        INSERT INTO parametros_nomina (
            anio_fiscal, isr_tramo1_hasta, isr_tramo2_hasta, isr_tramo3_hasta,
            salario_minimo_referencia, notas
        ) VALUES (
            2026, 416220.00, 624329.00, 867123.00,
            15000.00,
            'Valores de arranque (2026-08-26): estructura de 4 tramos ISR y tasas TSS confiables, pero los montos de corte de ISR y el salario minimo de referencia son representativos, no una consulta directa a DGII/TSS -- verificar contra la tabla vigente antes de nomina real.'
        )
        """
    )


def downgrade() -> None:
    op.get_bind().exec_driver_sql("DROP TABLE IF EXISTS parametros_nomina")
