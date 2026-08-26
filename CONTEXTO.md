# Contexto: sistema-af (nombre de trabajo — reemplazo de Soluflex)

Nombre de trabajo del repo/proyecto: **sistema-af**. Es provisional —
el nombre comercial de marca aún no está decidido (pendiente de
verificar disponibilidad en ONAPI). No bloquea el desarrollo; se
puede renombrar después sin fricción.

## Cliente y alcance
Reemplazo de Soluflex para dos empresas hermanas del mismo grupo:
**Agrocasa** (agroexportación de café/cacao) y **Creixa** (Inversiones
Creixa, SRL). Fase 1 cubre los 4 módulos: contabilidad, nómina,
facturación e inventario — todos con la misma prioridad.

## Stack decidido
- Backend: **FastAPI + PostgreSQL**
- Frontend: **React + Vite + TypeScript + Tailwind + shadcn/ui**
  (mismo stack que Mecanix, para reutilizar componentes)
- Arquitectura multi-tenant: **RLS de PostgreSQL**, mismo patrón que
  Mecanix (`app.tenant_id` fijado por request vía `SET LOCAL`)

## Archivos que acompañan este documento
- `schema_agrocasa_creixa.sql` — esquema completo, validado corriendo
  contra Postgres 16 real (19 tablas — corregido, el conteo de "24" de
  una version anterior de este documento no coincidia con los `CREATE
  TABLE` reales del archivo — RLS probado con dos tenants, trigger de
  cuadre de asientos). Punto de partida del repo.
- `catalogo_cuentas_agrocasa.csv` — catálogo real de 1400 cuentas
  exportado de la base Soluflex de Agrocasa. Se carga tal cual en
  `plan_cuentas`; el cliente lo depura después, no se reinterpreta.

## Decisiones ya tomadas (no reabrir sin razón)
1. Catálogo de cuentas: se usa el de Soluflex tal cual, sin depurar de
   antemano — el cliente lo hace directamente sobre el sistema nuevo.
2. Facturación: ambas — local (18% ITBIS) y exportación (0% ITBIS),
   vía e-CF. Soluflex nunca tuvo esto en uso real (`TIPOFE` nulo en
   todos sus tipos de documento), así que no hay dato histórico que
   migrar, es diseño nuevo.
3. Inventario: por finca/sucursal, con trazabilidad de lote de cosecha
   (café/cacao). Tampoco hay dato histórico (`LOTES`/`DLOTES` en 0 en
   ambas bases Soluflex).
4. `sucursales` fusiona lo que en un borrador previo se llamó
   "fincas/proyectos": verificado contra la tabla `SUCURSALES` real de
   Soluflex (Ocoa, Rancho Arriba, Santo Domingo) que ya representaba
   la misma entidad usada como centro de costo contable.

## Resuelto (2026-08-26) — nómina separada por empresa
**Ya no es una pregunta abierta.** Ver
`docs/designs/nucleo-contabilidad-nomina.md`, sección "Resolución
experta de Open Questions": la nómina es **separada por empresa**, no
compartida. Agrocasa y Creixa son entidades legales distintas (RNC
propio, registro TSS propio); cada `empleado` pertenece a una sola
`empresa_id` (ya es como está construido el schema — no requirió
cambio). Si una persona trabaja para ambas, se modela como dos filas de
`empleados` separadas, no como una nómina compartida. La tabla puente
`empleados_empresas` (N:M) que este documento dejaba como posibilidad
**no se construye** — quedó descartada, no pendiente.

## Hallazgos de la base histórica de Soluflex (para no reinterpretar)
- 1400 cuentas contables, patrón de asiento vía tabla `DETCONT`
  (id, origen, destino, cuenta, débito/crédito, monto) — inspiró el
  motor `asientos`/`asiento_detalle` de este esquema.
- Nómina ya distinguía fijos (con TSS) de jornaleros/temporeros
  (algunos sin TSS) en 10 tipos de nómina reales — confirma el diseño
  de `empleados.tipo_empleado` e `incluye_tss`.
- `GENTRANSNOM` (reglas nómina → cuenta contable) inspiró
  `reglas_contabilizacion`, generalizada aquí a cualquier módulo.
- Módulos sin uso real en Soluflex (0 registros en ambas bases):
  inventario, lotes, exportación, existencias. Confirma que estos
  módulos son diseño nuevo, no migración.

## Seguridad multi-tenant — checklist para implementar (no está en el SQL)
Ver sección final de `schema_agrocasa_creixa.sql` para el detalle
completo. Resumen:
- Middleware FastAPI que fija `app.tenant_id` desde el JWT antes de
  cualquier query — debe fallar cerrado (rechazar el request) si el
  JWT no trae un tenant_id válido, nunca usar un default.
- Verificar comportamiento de `SET LOCAL` con pgbouncer si se usa en
  modo *transaction pooling*.
- Rol de aplicación (`app_user`) separado del owner de las tablas —
  `FORCE ROW LEVEL SECURITY` no aplica al owner.
- Rol de soporte aparte con `BYPASSRLS` para consultas cross-tenant,
  cada uso debe quedar en `auditoria`.
