# TODOs — sistema-af

## Endurecer seguridad multi-tenant para segundo tenant real

**What:** Implementar compatibilidad de `SET LOCAL app.tenant_id` con pgbouncer en modo transaction pooling, y crear el rol de soporte con `BYPASSRLS` auditado (cada uso queda registrado en `auditoria`).

**Why:** Hoy sistema-af tiene un solo tenant real (Agrocasa/Creixa). El checklist de seguridad multi-tenant de CONTEXTO.md marca esto como pendiente de implementar, y el design doc de contabilidad/nómina (`docs/designs/nucleo-contabilidad-nomina.md`) lo clasificó explícitamente como "diferible hasta que exista un segundo tenant real" — construir esto ahora sería seguridad para un escenario que todavía no existe.

**Pros:**
- Evita invertir tiempo en infraestructura de aislamiento cross-tenant que ningún tenant actual necesita.
- El middleware fail-closed de `app.tenant_id` (must-have, ya priorizado) cubre el riesgo real de hoy con un solo tenant.

**Cons:**
- Si se olvida, el día que se dé de alta un segundo tenant real (el propio schema fue diseñado como SaaS multi-tenant, "cada tenant es un cliente tuyo"), no habrá rol de soporte auditable para diagnósticos cross-tenant ni garantía de que `SET LOCAL` se re-emita correctamente si en ese momento se usa pgbouncer en modo transaction pooling — el vector de fuga entre tenants más común en este patrón de arquitectura, según el propio checklist de CONTEXTO.md.

**Context:** Ver CONTEXTO.md, sección "Seguridad multi-tenant — checklist para implementar", puntos B y D. Ver también `docs/designs/nucleo-contabilidad-nomina.md`, sección Dependencies, para la decisión de diferir esto tomada en la revisión de arquitectura (plan-eng-review) del 2026-08-25.

**Depends on / blocked by:** Bloqueado en la práctica hasta que exista un segundo tenant real dado de alta. No depende de ningún otro trabajo pendiente.
