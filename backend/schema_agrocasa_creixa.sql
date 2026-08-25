-- =====================================================================
-- ESQUEMA: Sistema SaaS multi-tenant (reemplazo de Soluflex)
-- Basado en: catálogo de cuentas real (1400 ctas), patrón de asientos
--            (DETCONT), reglas de nómina (GENTRANSNOM), y hallazgo de
--            centro de costo por finca (sufijo "-23" en Creixa).
-- Facturación e-CF e inventario por finca: diseño nuevo, sin dato
--            histórico de Soluflex que reutilizar (TIPOFE nulo, LOTES=0).
-- Multi-tenant: aislamiento vía RLS de PostgreSQL, mismo patrón que
--            Mecanix. Cada tenant es un cliente tuyo (ej. el grupo
--            Agrocasa/Creixa); dentro de un tenant puede haber varias
--            empresas legales (RNC distintos).
-- Pendiente: confirmar con cliente si nómina es compartida o separada
--            entre Agrocasa y Creixa (ver notas en tabla empleados).
-- =====================================================================

-- ── TENANTS ────────────────────────────────────────────────────────────

CREATE TABLE tenants (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre          VARCHAR(150) NOT NULL,
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Variable de sesión que fija el tenant activo por conexión.
-- El backend la asigna al abrir cada request autenticado:
--   SET app.tenant_id = '<uuid-del-tenant>';
-- Todas las políticas RLS de abajo filtran contra esta variable.

-- ── EMPRESAS Y CENTROS DE COSTO ──────────────────────────────────────

CREATE TABLE empresas (
    id              SERIAL PRIMARY KEY,
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    rnc             VARCHAR(20) NOT NULL,
    razon_social    VARCHAR(150) NOT NULL,
    nombre_comercial VARCHAR(100),
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, rnc)
);

-- Reemplaza el truco de sufijo "-23" en nombres de cuenta visto en Creixa,
-- Y corresponde 1:1 a la tabla SUCURSALES real de Soluflex (verificado:
-- 4 registros — OCOA, RANCHO ARRIBA, SANTO DOMINGO — mismos nombres que
-- aparecían como centro de costo y como tipo de nómina). Una sucursal
-- puede ser una finca (centro de costo agrícola), una oficina
-- administrativa, o un proyecto puntual.
CREATE TABLE sucursales (
    id              SERIAL PRIMARY KEY,
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    empresa_id      INTEGER NOT NULL REFERENCES empresas(id),
    codigo          VARCHAR(20) NOT NULL,
    nombre          VARCHAR(150) NOT NULL,
    tipo            VARCHAR(20) NOT NULL CHECK (tipo IN ('finca','oficina','proyecto')),
    direccion       VARCHAR(200),
    gerente         VARCHAR(150),
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (empresa_id, codigo)
);

-- Corresponde a ALMACENES de Soluflex (verificado: 2 registros, cada uno
-- ligado a una sucursal). Necesario para inventario: una sucursal puede
-- tener más de un almacén físico.
CREATE TABLE almacenes (
    id              SERIAL PRIMARY KEY,
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    sucursal_id     INTEGER NOT NULL REFERENCES sucursales(id),
    codigo          VARCHAR(20) NOT NULL,
    nombre          VARCHAR(150) NOT NULL,
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (sucursal_id, codigo)
);

-- ── CATÁLOGO DE CUENTAS (importado de Soluflex, sin depurar) ─────────
-- Por tenant: cada cliente trae su propio catálogo al migrar.

CREATE TABLE plan_cuentas (
    id              SERIAL PRIMARY KEY,
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    numero_cta      VARCHAR(20) NOT NULL,           -- tal cual Soluflex, incl. sufijos "-NN"
    nivel           SMALLINT NOT NULL,
    tipo_cta        SMALLINT NOT NULL,               -- 1 Activo 2 Pasivo 3 Patrimonio 4 Ingreso 5 Costo 6 Gasto
    nombre          VARCHAR(200) NOT NULL,
    -- El cliente depurará este catálogo directamente; se deja como
    -- carga inicial 1:1 del CSV exportado, sin reinterpretar jerarquía.
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (tenant_id, numero_cta)
);

-- ── MOTOR DE ASIENTOS CENTRALIZADO (equivalente a DETCONT) ───────────

CREATE TABLE asientos (
    id              BIGSERIAL PRIMARY KEY,
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    empresa_id      INTEGER NOT NULL REFERENCES empresas(id),
    fecha           DATE NOT NULL,
    origen_tipo     VARCHAR(20) NOT NULL CHECK (origen_tipo IN ('factura','nomina','manual','inventario')),
    origen_id       BIGINT,                          -- FK lógica a factura/nomina/etc, según origen_tipo
    descripcion     VARCHAR(250),
    creado_por      VARCHAR(100),
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE asiento_detalle (
    id              BIGSERIAL PRIMARY KEY,
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    asiento_id      BIGINT NOT NULL REFERENCES asientos(id) ON DELETE CASCADE,
    numero_cta      VARCHAR(20) NOT NULL,
    sucursal_id     INTEGER REFERENCES sucursales(id),  -- dimensión de costeo, opcional
    debcred         CHAR(1) NOT NULL CHECK (debcred IN ('D','C')),
    monto           NUMERIC(18,2) NOT NULL CHECK (monto > 0),
    FOREIGN KEY (tenant_id, numero_cta) REFERENCES plan_cuentas(tenant_id, numero_cta)
);

-- Constraint de integridad que Soluflex no forzaba a nivel de motor:
-- cada asiento debe cuadrar (suma débitos = suma créditos).
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
-- Se dispara AFTER para permitir insertar ambas líneas antes de validar;
-- en la app, insertar todas las líneas del asiento en una sola transacción.
CREATE CONSTRAINT TRIGGER trg_cuadre_asiento
    AFTER INSERT OR UPDATE OR DELETE ON asiento_detalle
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION fn_validar_cuadre_asiento();

-- ── REGLAS DE MAPEO (equivalente a GENTRANSNOM, generalizado) ────────
-- En vez de una tabla solo para nómina, se generaliza a cualquier origen
-- (nómina, factura) para no duplicar el patrón por módulo. Por tenant,
-- ya que cada cliente define sus propias reglas contables.

CREATE TABLE reglas_contabilizacion (
    id              SERIAL PRIMARY KEY,
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    origen_tipo     VARCHAR(20) NOT NULL,            -- 'nomina','factura_local','factura_exportacion'
    codigo_evento   VARCHAR(30) NOT NULL,             -- p.ej. 'JORNALES_COSECHA', 'VENTA_EXPORT', 'ITBIS_18'
    numero_cta      VARCHAR(20) NOT NULL,
    debcred         CHAR(1) NOT NULL CHECK (debcred IN ('D','C')),
    UNIQUE (tenant_id, origen_tipo, codigo_evento, numero_cta),
    FOREIGN KEY (tenant_id, numero_cta) REFERENCES plan_cuentas(tenant_id, numero_cta)
);

-- ── EMPLEADOS Y NÓMINA ────────────────────────────────────────────────
-- PENDIENTE DEL CLIENTE: si nómina es compartida o separada por empresa.
-- Diseño actual: empleado pertenece a una empresa base (empresa_id),
-- pero cada línea de nómina lleva su propia sucursal_id, lo que
-- ya permite prorrateo entre fincas de una misma empresa. Si el cliente
-- confirma que un empleado puede trabajar para ambas empresas, se
-- agrega una tabla puente empleados_empresas (N:M) sin romper lo demás.

CREATE TABLE empleados (
    id              SERIAL PRIMARY KEY,
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    empresa_id      INTEGER NOT NULL REFERENCES empresas(id),
    sucursal_id     INTEGER REFERENCES sucursales(id),  -- sucursal base del empleado
    cedula          VARCHAR(15),
    nombre_completo VARCHAR(150) NOT NULL,
    tipo_empleado   VARCHAR(15) NOT NULL CHECK (tipo_empleado IN ('fijo','jornalero')),
    incluye_tss     BOOLEAN NOT NULL DEFAULT TRUE,   -- refleja INCATSS visto en Soluflex
    salario_base    NUMERIC(14,2),                   -- para 'fijo'
    tarifa_unidad   NUMERIC(14,2),                   -- para 'jornalero' (pago por tarea/día)
    fecha_ingreso   DATE,
    fecha_salida    DATE,
    activo          BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE nomina_corridas (
    id              SERIAL PRIMARY KEY,
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    empresa_id      INTEGER NOT NULL REFERENCES empresas(id),
    sucursal_id     INTEGER REFERENCES sucursales(id),  -- NULL si es corrida multi-sucursal
    codigo          VARCHAR(10) NOT NULL,             -- equivalente a CODNOM de Soluflex
    nombre          VARCHAR(100) NOT NULL,            -- p.ej. "Nómina quincenal", "Nómina obreros Ocoa"
    periodo_inicio  DATE NOT NULL,
    periodo_fin     DATE NOT NULL,
    incluye_tss     BOOLEAN NOT NULL DEFAULT TRUE,
    cerrada         BOOLEAN NOT NULL DEFAULT FALSE,
    asiento_id      BIGINT REFERENCES asientos(id)   -- asiento generado al postear
);

CREATE TABLE nomina_detalle (
    id              BIGSERIAL PRIMARY KEY,
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    nomina_corrida_id INTEGER NOT NULL REFERENCES nomina_corridas(id) ON DELETE CASCADE,
    empleado_id     INTEGER NOT NULL REFERENCES empleados(id),
    sucursal_id     INTEGER REFERENCES sucursales(id),  -- para prorrateo a costo de cosecha
    dias_unidades   NUMERIC(8,2),                     -- días trabajados o tareas (jornaleros)
    monto_bruto     NUMERIC(14,2) NOT NULL,
    retencion_isr   NUMERIC(14,2) NOT NULL DEFAULT 0,
    retencion_tss   NUMERIC(14,2) NOT NULL DEFAULT 0,  -- SFS + AFP
    monto_neto      NUMERIC(14,2) NOT NULL
);

-- ── INVENTARIO POR FINCA / LOTE ──────────────────────────────────────
-- Diseño nuevo: Soluflex nunca tuvo esto en uso (LOTES=0, DLOTES=0).

CREATE TABLE lotes_cosecha (
    id              SERIAL PRIMARY KEY,
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    sucursal_id     INTEGER NOT NULL REFERENCES sucursales(id),  -- finca de origen
    almacen_id      INTEGER REFERENCES almacenes(id),            -- almacén donde reposa actualmente
    producto        VARCHAR(50) NOT NULL,             -- 'cafe','cacao'
    fecha_cosecha   DATE NOT NULL,
    cantidad        NUMERIC(14,2) NOT NULL,
    unidad          VARCHAR(10) NOT NULL DEFAULT 'qq', -- quintales
    calidad_grado   VARCHAR(30),
    humedad_pct     NUMERIC(5,2),
    costo_acumulado NUMERIC(14,2) NOT NULL DEFAULT 0,  -- alimentado desde nomina_detalle por finca
    estado          VARCHAR(20) NOT NULL DEFAULT 'disponible'
                        CHECK (estado IN ('disponible','en_proceso','vendido','exportado'))
);

CREATE TABLE inventario_movimientos (
    id              BIGSERIAL PRIMARY KEY,
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    lote_id         INTEGER NOT NULL REFERENCES lotes_cosecha(id),
    tipo_movimiento VARCHAR(20) NOT NULL CHECK (tipo_movimiento IN ('entrada','salida','ajuste','merma','traslado')),
    almacen_origen_id  INTEGER REFERENCES almacenes(id),   -- usado en 'salida' y 'traslado'
    almacen_destino_id INTEGER REFERENCES almacenes(id),   -- usado en 'entrada' y 'traslado'
    cantidad        NUMERIC(14,2) NOT NULL,
    referencia_doc  VARCHAR(50),                      -- factura o conduce asociado
    fecha           DATE NOT NULL,
    asiento_id      BIGINT REFERENCES asientos(id)
);

-- ── FACTURACIÓN ELECTRÓNICA (e-CF) ───────────────────────────────────
-- Diseño nuevo: TIPOFE nulo en todo Soluflex, sin dato que reutilizar.
-- Campos DGIICOMP/DGIIVENTAS/EMBARQUE de ENTDOC se toman como señal de
-- intención (exportación) pero no como estructura de datos real.

CREATE TABLE clientes (
    id              SERIAL PRIMARY KEY,
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    empresa_id      INTEGER NOT NULL REFERENCES empresas(id),
    rnc_cedula      VARCHAR(20),
    nombre          VARCHAR(150) NOT NULL,
    pais            VARCHAR(60) NOT NULL DEFAULT 'República Dominicana',
    es_exterior     BOOLEAN NOT NULL DEFAULT FALSE     -- true = cliente de exportación
);

CREATE TABLE facturas (
    id              BIGSERIAL PRIMARY KEY,
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    empresa_id      INTEGER NOT NULL REFERENCES empresas(id),
    sucursal_id     INTEGER NOT NULL REFERENCES sucursales(id),  -- desde dónde se emite (define secuencia e-CF)
    cliente_id      INTEGER NOT NULL REFERENCES clientes(id),
    tipo_factura    VARCHAR(20) NOT NULL CHECK (tipo_factura IN ('local','exportacion')),
    e_ncf           VARCHAR(20),                       -- número e-CF asignado por el proveedor autorizado
    tipo_ecf        VARCHAR(5),                         -- '31' crédito fiscal, '32' consumo, '46' exportación, etc.
    fecha_emision   DATE NOT NULL,
    moneda          VARCHAR(3) NOT NULL DEFAULT 'DOP',  -- exportación probablemente en USD
    subtotal        NUMERIC(14,2) NOT NULL,
    itbis_pct       NUMERIC(5,2) NOT NULL DEFAULT 0,    -- 0 para exportación, 18 para local
    itbis_monto     NUMERIC(14,2) NOT NULL DEFAULT 0,
    total           NUMERIC(14,2) NOT NULL,
    estado_ecf      VARCHAR(20) NOT NULL DEFAULT 'pendiente'
                        CHECK (estado_ecf IN ('pendiente','aceptado','rechazado','no_aplica')),
    lote_id         INTEGER REFERENCES lotes_cosecha(id),  -- de qué lote sale la exportación
    asiento_id      BIGINT REFERENCES asientos(id)   -- se genera solo si estado_ecf en ('aceptado','no_aplica')
);

CREATE TABLE factura_detalle (
    id              BIGSERIAL PRIMARY KEY,
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    factura_id      BIGINT NOT NULL REFERENCES facturas(id) ON DELETE CASCADE,
    descripcion     VARCHAR(200) NOT NULL,
    cantidad        NUMERIC(14,2) NOT NULL,
    precio_unitario NUMERIC(14,2) NOT NULL,
    monto           NUMERIC(14,2) NOT NULL
);

-- ── USUARIOS Y ROLES ──────────────────────────────────────────────────

CREATE TABLE usuarios (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    empresa_id      INTEGER REFERENCES empresas(id),   -- NULL si tiene acceso a todas las empresas del tenant
    email           VARCHAR(150) NOT NULL,
    nombre_completo VARCHAR(150) NOT NULL,
    hash_password   VARCHAR(200) NOT NULL,
    rol             VARCHAR(20) NOT NULL CHECK (rol IN ('admin','contador','nomina','facturacion','consulta')),
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, email)
);

-- ── SECUENCIAS DE COMPROBANTE FISCAL (e-CF) ──────────────────────────
-- Un tenant puede tener varias sucursales, y cada una su propia
-- secuencia autorizada por DGII para cada tipo de e-CF. Nunca se
-- comparte numeración entre tenants ni entre sucursales.

CREATE TABLE secuencias_ecf (
    id              SERIAL PRIMARY KEY,
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    sucursal_id     INTEGER NOT NULL REFERENCES sucursales(id),
    tipo_ecf        VARCHAR(5) NOT NULL,               -- '31','32','46', etc.
    proximo_numero  BIGINT NOT NULL DEFAULT 1,
    numero_max      BIGINT NOT NULL,                    -- límite autorizado por DGII
    fecha_vencimiento DATE,
    UNIQUE (tenant_id, sucursal_id, tipo_ecf)
);

-- ── AUDITORÍA ─────────────────────────────────────────────────────────
-- Registro de acciones sensibles. Es también la red de seguridad para
-- detectar una fuga entre tenants si el middleware de app.tenant_id
-- falla: cualquier acceso cruzado debería quedar visible aquí.

CREATE TABLE auditoria (
    id              BIGSERIAL PRIMARY KEY,
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    usuario_id      UUID REFERENCES usuarios(id),
    accion          VARCHAR(50) NOT NULL,               -- 'crear','modificar','eliminar','postear_asiento', etc.
    tabla_afectada  VARCHAR(50) NOT NULL,
    registro_id     VARCHAR(50),
    detalle         JSONB,                               -- diff antes/después
    ip_origen       INET,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================================
-- ROW LEVEL SECURITY (aislamiento multi-tenant)
-- =====================================================================
-- Mismo patrón que Mecanix: el backend fija app.tenant_id por
-- conexión/request y Postgres filtra automáticamente. Ninguna consulta
-- de la aplicación necesita (ni debe) agregar WHERE tenant_id = ... a
-- mano; RLS lo garantiza aunque el código de la app tenga un bug.

DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN
        SELECT unnest(ARRAY[
            'empresas','sucursales','almacenes','plan_cuentas','asientos',
            'asiento_detalle','reglas_contabilizacion','empleados',
            'nomina_corridas','nomina_detalle','lotes_cosecha',
            'inventario_movimientos','clientes','facturas','factura_detalle',
            'usuarios','secuencias_ecf','auditoria'
        ])
    LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
        EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', t);
        EXECUTE format(
            'CREATE POLICY tenant_isolation ON %I
                USING (tenant_id = current_setting(''app.tenant_id'')::uuid)
                WITH CHECK (tenant_id = current_setting(''app.tenant_id'')::uuid)',
            t
        );
    END LOOP;
END $$;

-- El rol de aplicación (no el propietario de las tablas) es el que debe
-- conectarse en runtime, para que FORCE ROW LEVEL SECURITY realmente
-- aplique (el owner de la tabla la ignora por defecto):
--   CREATE ROLE app_user LOGIN PASSWORD '...';
--   GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
-- Y en cada request del backend (FastAPI, vía dependencia):
--   SET LOCAL app.tenant_id = '<uuid>';

-- =====================================================================
-- NOTAS DE DISEÑO
-- =====================================================================
-- 1. asientos/asiento_detalle es el único punto de escritura
--    contable. Nómina, facturación e inventario NO escriben en
--    plan_cuentas directamente: generan sus filas y el backend arma el
--    asiento vía reglas_contabilizacion.
-- 2. El constraint de cuadre (trg_cuadre_asiento) reemplaza el "DESCUADRE"
--    que Soluflex solo registraba como bandera informativa (campo
--    ENTDOC.DESCUADRE) sin bloquear. Aquí sí bloquea.
-- 3. Para e-CF real hace falta contratar/confirmar el proveedor
--    autorizado (OFV/DGII) e integrar su API — no es parte de este
--    esquema, que solo modela el resultado (e_ncf, estado_ecf).
-- 4. Catálogo de cuentas: cargar tal cual el CSV exportado de Soluflex
--    (1400 filas) sin reinterpretar; el cliente lo depura después. Por
--    tenant, ya que cada cliente nuevo del SaaS trae el suyo.
-- 5. tenant_id vive en cada tabla (denormalizado) en vez de solo en
--    empresas, para que las políticas RLS no necesiten JOIN — más
--    simple y más rápido a nivel de motor.
-- 6. sucursales fusiona lo que en un borrador previo se llamó
--    "fincas_proyectos": verificado contra Soluflex que SUCURSALES
--    (4 registros: Ocoa, Rancho Arriba, Santo Domingo) ya representaba
--    la misma entidad que el centro de costo contable. Evita que el
--    cliente registre "Ocoa" dos veces bajo dos conceptos distintos.
--    almacenes cuelga de sucursal (equivalente a ALMACENES de Soluflex,
--    2 registros reales, cada uno ligado a una sucursal).
-- =====================================================================

-- =====================================================================
-- CHECKLIST DE ARQUITECTURA MULTI-TENANT (para implementar en Code,
-- no son parte del DDL de este archivo)
-- =====================================================================
-- A. Middleware de tenant (crítico): dependency de FastAPI que, en cada
--    request autenticado, decodifica el tenant_id del JWT y ejecuta
--    SET LOCAL app.tenant_id ANTES de cualquier query. Si el JWT no
--    trae tenant_id válido, la request se rechaza — nunca un default
--    ni fallback a un tenant fijo (el hallazgo de "fail-open" y
--    "fallback silencioso a tenant hardcodeado" de la auditoría de
--    Mecanix es exactamente el error a no repetir aquí).
-- B. Pooling de conexiones: SET LOCAL solo vale dentro de una misma
--    transacción/conexión física. Si se usa pgbouncer en modo
--    transaction pooling, confirmar que el SET LOCAL se re-emite en
--    cada transacción — es la causa más común de fuga entre tenants
--    en este tipo de arquitectura.
-- C. Aprovisionamiento: script/endpoint admin para dar de alta un
--    tenant nuevo (tenant + empresa(s) + carga inicial de plan_cuentas)
--    en vez de INSERT manual cada vez.
-- D. Acceso de soporte cross-tenant: rol Postgres separado con
--    BYPASSRLS, nunca el mismo rol de aplicación, y cada uso de ese
--    rol debe quedar escrito en auditoria.
-- =====================================================================

