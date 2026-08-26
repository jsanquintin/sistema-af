"""estado de asientos (borrador/posteado) + catalogo de cuentas por empresa

Revision ID: 0003_asientos_estado_empresa
Revises: 0002_asiento_tenant_idx
Create Date: 2026-08-26

Implementa las decisiones de la seccion "Resolucion experta de Open
Questions (2026-08-26)" en docs/designs/nucleo-contabilidad-nomina.md
(Open Questions 3, 5 y 9):

1. asientos gana una columna estado ('borrador'|'posteado'). El trigger
   de cuadre (fn_validar_cuadre_asiento) deja de calcular debe/haber --
   esa validacion se mueve a app/services/contabilizacion.py:postear_asiento,
   que corre ANTES de marcar un asiento como posteado. El trigger ahora
   solo hace cumplir inmutabilidad: ninguna fila de asiento_detalle de un
   asiento ya posteado puede insertarse/editarse/borrarse -- la correccion
   real es un asiento de reverso, nunca un UPDATE sobre uno posteado.
2. plan_cuentas y reglas_contabilizacion pasan a tener catalogo/reglas por
   empresa (antes eran solo por tenant) -- Agrocasa (agroexportacion) y
   Creixa (inversiones) son giros de negocio sin overlap real de cuentas.
   asiento_detalle gana su propia columna empresa_id (denormalizada desde
   asientos.empresa_id, mismo patron que tenant_id ya denormalizado en
   todo el schema) porque su FK compuesto contra plan_cuentas ahora
   necesita empresa_id para resolver la fila correcta.

Los nombres de constraints que ya existian en el schema original (no
creados por esta migracion) se buscan dinamicamente via pg_constraint en
vez de asumir el nombre exacto que Postgres les puso -- el nombre
autogenerado de un UNIQUE/FOREIGN KEY con varias columnas se trunca o
sufija de forma que no es seguro adivinar sin consultar la base real.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0003_asientos_estado_empresa"
down_revision: Union[str, None] = "0002_asiento_tenant_idx"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_DROP_ORIGEN_TIPO_CHECK = """
DO $$
DECLARE
    v_conname TEXT;
BEGIN
    SELECT conname INTO v_conname
    FROM pg_constraint
    WHERE conrelid = 'asientos'::regclass
      AND contype = 'c'
      AND pg_get_constraintdef(oid) LIKE '%origen_tipo%';
    EXECUTE format('ALTER TABLE asientos DROP CONSTRAINT %I', v_conname);
END $$;
"""

_DROP_PLAN_CUENTAS_UNIQUE = """
DO $$
DECLARE
    v_conname TEXT;
BEGIN
    SELECT conname INTO v_conname
    FROM pg_constraint
    WHERE conrelid = 'plan_cuentas'::regclass AND contype = 'u';
    EXECUTE format('ALTER TABLE plan_cuentas DROP CONSTRAINT %I', v_conname);
END $$;
"""

_DROP_REGLAS_UNIQUE = """
DO $$
DECLARE
    v_conname TEXT;
BEGIN
    SELECT conname INTO v_conname
    FROM pg_constraint
    WHERE conrelid = 'reglas_contabilizacion'::regclass AND contype = 'u';
    EXECUTE format('ALTER TABLE reglas_contabilizacion DROP CONSTRAINT %I', v_conname);
END $$;
"""

_DROP_ASIENTO_DETALLE_PLAN_CUENTAS_FKEY = """
DO $$
DECLARE
    v_conname TEXT;
BEGIN
    SELECT conname INTO v_conname
    FROM pg_constraint
    WHERE conrelid = 'asiento_detalle'::regclass
      AND confrelid = 'plan_cuentas'::regclass
      AND contype = 'f';
    EXECUTE format('ALTER TABLE asiento_detalle DROP CONSTRAINT %I', v_conname);
END $$;
"""

_DROP_REGLAS_PLAN_CUENTAS_FKEY = """
DO $$
DECLARE
    v_conname TEXT;
BEGIN
    SELECT conname INTO v_conname
    FROM pg_constraint
    WHERE conrelid = 'reglas_contabilizacion'::regclass
      AND confrelid = 'plan_cuentas'::regclass
      AND contype = 'f';
    EXECUTE format('ALTER TABLE reglas_contabilizacion DROP CONSTRAINT %I', v_conname);
END $$;
"""

_FN_VALIDAR_ASIENTO_NUEVA = """
CREATE OR REPLACE FUNCTION fn_validar_cuadre_asiento() RETURNS TRIGGER AS $$
DECLARE
    v_estado VARCHAR(10);
BEGIN
    -- El cuadre (debe=haber) ya no se valida aqui -- se mueve a
    -- app/services/contabilizacion.py:postear_asiento, que corre antes de
    -- marcar el asiento como 'posteado'. Este trigger ahora solo protege
    -- inmutabilidad: un asiento posteado no admite ninguna modificacion a
    -- sus lineas, cuadre o no.
    SELECT estado INTO v_estado FROM asientos WHERE id = COALESCE(NEW.asiento_id, OLD.asiento_id);

    IF v_estado = 'posteado' THEN
        RAISE EXCEPTION 'Asiento % ya esta posteado -- es inmutable, corrija con un asiento de reverso',
            COALESCE(NEW.asiento_id, OLD.asiento_id);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

_FN_VALIDAR_ASIENTO_ORIGINAL = """
CREATE OR REPLACE FUNCTION fn_validar_cuadre_asiento() RETURNS TRIGGER AS $$
DECLARE
    v_debe NUMERIC(18,2);
    v_haber NUMERIC(18,2);
BEGIN
    SELECT COALESCE(SUM(CASE WHEN debcred='D' THEN monto ELSE 0 END),0),
           COALESCE(SUM(CASE WHEN debcred='C' THEN monto ELSE 0 END),0)
    INTO v_debe, v_haber
    FROM asiento_detalle
    WHERE asiento_id = COALESCE(NEW.asiento_id, OLD.asiento_id);

    IF v_debe <> v_haber THEN
        RAISE EXCEPTION 'Asiento % descuadrado: debe=% haber=%',
            COALESCE(NEW.asiento_id, OLD.asiento_id), v_debe, v_haber;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    bind = op.get_bind()

    def run(sql: str) -> None:
        # Mismo motivo que 0001_initial_schema: exec_driver_sql manda un
        # objeto de parametros vacio y psycopg2 interpreta cualquier "%"
        # suelto (RAISE EXCEPTION, format('%I', ...)) como su propio
        # placeholder si no se escapa como "%%".
        bind.exec_driver_sql(sql.replace("%", "%%"))

    # 1) estado de asientos + origen_tipo con 'apertura'
    run("ALTER TABLE asientos ADD COLUMN estado VARCHAR(10) NOT NULL DEFAULT 'borrador'")
    run(
        "ALTER TABLE asientos ADD CONSTRAINT asientos_estado_check "
        "CHECK (estado IN ('borrador','posteado'))"
    )
    run(_DROP_ORIGEN_TIPO_CHECK)
    run(
        "ALTER TABLE asientos ADD CONSTRAINT asientos_origen_tipo_check "
        "CHECK (origen_tipo IN ('factura','nomina','manual','inventario','apertura'))"
    )

    # 2) asiento_detalle.empresa_id, denormalizado desde asientos.empresa_id
    run("ALTER TABLE asiento_detalle ADD COLUMN empresa_id INTEGER REFERENCES empresas(id)")
    run(
        "UPDATE asiento_detalle ad SET empresa_id = a.empresa_id "
        "FROM asientos a WHERE a.id = ad.asiento_id"
    )
    run("ALTER TABLE asiento_detalle ALTER COLUMN empresa_id SET NOT NULL")

    # 3) plan_cuentas por empresa. Sin backfill automatico a proposito: si
    # ya hay filas cargadas bajo el esquema viejo, SET NOT NULL falla aqui
    # y obliga a resolver a mano cual empresa le corresponde a cada una en
    # vez de asumir una -- en este entorno de trabajo no hay filas reales.
    run("ALTER TABLE plan_cuentas ADD COLUMN empresa_id INTEGER REFERENCES empresas(id)")
    run(_DROP_PLAN_CUENTAS_UNIQUE)
    run("ALTER TABLE plan_cuentas ALTER COLUMN empresa_id SET NOT NULL")
    run(
        "ALTER TABLE plan_cuentas ADD CONSTRAINT plan_cuentas_tenant_empresa_numero_cta_key "
        "UNIQUE (tenant_id, empresa_id, numero_cta)"
    )
    run("CREATE INDEX ix_plan_cuentas_tenant_empresa ON plan_cuentas (tenant_id, empresa_id)")

    # 4) reglas_contabilizacion por empresa (mismo motivo)
    run("ALTER TABLE reglas_contabilizacion ADD COLUMN empresa_id INTEGER REFERENCES empresas(id)")
    run(_DROP_REGLAS_UNIQUE)
    run("ALTER TABLE reglas_contabilizacion ALTER COLUMN empresa_id SET NOT NULL")
    run(
        "ALTER TABLE reglas_contabilizacion "
        "ADD CONSTRAINT reglas_contabilizacion_tenant_empresa_evento_cta_key "
        "UNIQUE (tenant_id, empresa_id, origen_tipo, codigo_evento, numero_cta)"
    )
    run(
        "CREATE INDEX ix_reglas_contabilizacion_tenant_empresa "
        "ON reglas_contabilizacion (tenant_id, empresa_id)"
    )

    # 5) FKs compuestos contra plan_cuentas ahora incluyen empresa_id
    run(_DROP_ASIENTO_DETALLE_PLAN_CUENTAS_FKEY)
    run(
        "ALTER TABLE asiento_detalle ADD CONSTRAINT asiento_detalle_plan_cuentas_fkey "
        "FOREIGN KEY (tenant_id, empresa_id, numero_cta) "
        "REFERENCES plan_cuentas (tenant_id, empresa_id, numero_cta)"
    )
    run(_DROP_REGLAS_PLAN_CUENTAS_FKEY)
    run(
        "ALTER TABLE reglas_contabilizacion ADD CONSTRAINT reglas_contabilizacion_plan_cuentas_fkey "
        "FOREIGN KEY (tenant_id, empresa_id, numero_cta) "
        "REFERENCES plan_cuentas (tenant_id, empresa_id, numero_cta)"
    )

    # 6) trigger de cuadre -> trigger de inmutabilidad (misma funcion, mismo
    # trigger trg_cuadre_asiento ya creado en 0001, no hace falta recrearlo)
    run(_FN_VALIDAR_ASIENTO_NUEVA)


def downgrade() -> None:
    bind = op.get_bind()

    def run(sql: str) -> None:
        bind.exec_driver_sql(sql.replace("%", "%%"))

    run(_FN_VALIDAR_ASIENTO_ORIGINAL)

    run(
        "ALTER TABLE reglas_contabilizacion DROP CONSTRAINT reglas_contabilizacion_plan_cuentas_fkey"
    )
    run("ALTER TABLE asiento_detalle DROP CONSTRAINT asiento_detalle_plan_cuentas_fkey")

    run("DROP INDEX IF EXISTS ix_reglas_contabilizacion_tenant_empresa")
    run(
        "ALTER TABLE reglas_contabilizacion "
        "DROP CONSTRAINT reglas_contabilizacion_tenant_empresa_evento_cta_key"
    )
    run(
        "ALTER TABLE reglas_contabilizacion "
        "ADD CONSTRAINT reglas_contabilizacion_tenant_evento_cta_key "
        "UNIQUE (tenant_id, origen_tipo, codigo_evento, numero_cta)"
    )
    run("ALTER TABLE reglas_contabilizacion DROP COLUMN empresa_id")

    run("DROP INDEX IF EXISTS ix_plan_cuentas_tenant_empresa")
    run("ALTER TABLE plan_cuentas DROP CONSTRAINT plan_cuentas_tenant_empresa_numero_cta_key")
    run(
        "ALTER TABLE plan_cuentas ADD CONSTRAINT plan_cuentas_tenant_id_numero_cta_key "
        "UNIQUE (tenant_id, numero_cta)"
    )
    run("ALTER TABLE plan_cuentas DROP COLUMN empresa_id")

    run("ALTER TABLE asiento_detalle DROP COLUMN empresa_id")

    run("ALTER TABLE asientos DROP CONSTRAINT asientos_origen_tipo_check")
    run(
        "ALTER TABLE asientos ADD CONSTRAINT asientos_origen_tipo_check "
        "CHECK (origen_tipo IN ('factura','nomina','manual','inventario'))"
    )
    run("ALTER TABLE asientos DROP CONSTRAINT asientos_estado_check")
    run("ALTER TABLE asientos DROP COLUMN estado")
