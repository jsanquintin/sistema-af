# Panel de superadmin multi-tenant

**Fecha:** 2026-08-27
**Contexto:** revisión de arquitectura (`/plan-eng-review` + `/office-hours` inline) antes de implementar.

## Por qué ahora

`docs/designs/nucleo-contabilidad-nomina.md` (2026-08-25) había diferido explícitamente el
endurecimiento multi-tenant "hasta que exista un segundo tenant real" — hoy sistema-af tiene
un solo tenant (`Agrocasa/Creixa`, ver `backend/scripts/seed_tenant.py`). El dueño confirmó
que un segundo cliente real está por darse de alta, y que van a venir más después. Esa es
exactamente la condición que el proyecto ya había fijado como disparador. Este documento
diseña el panel que permite dar de alta y administrar tenants sin pasar por un script de
línea de comandos cada vez.

## Alcance confirmado con el dueño

Versión completa, no un MVP recortado — confirmado explícitamente ("no vamos a trabajar 2
veces"):
- Alta de tenants desde una UI (reemplaza `seed_tenant.py` para el uso recurrente).
- Listado y activación/desactivación de tenants.
- Impersonation real: el superadmin entra a operar dentro de cualquier tenant sin conocer
  la contraseña de un usuario de ese tenant.

## Decisión de arquitectura: control plane separado (Approach B)

Alternativas consideradas:

| | Modelo | Riesgo | Por qué se descartó / eligió |
|---|---|---|---|
| A | Flag `es_superadmin` + `tenant_id` nullable en `Usuario` | Medio-alto | Toca el invariante de seguridad más sensible del sistema (`tenant_id NOT NULL` es la base de `get_tenant_db`/RLS) para el caso más peligroso (un rol que cruza tenants). |
| **B** | **Tabla `superadmins` separada, login propio, sin tocar `usuarios`** | **Bajo** | **Elegida.** Separación estructural: un bug en el código de superadmin no puede debilitar el aislamiento entre tenants porque no comparte tabla, JWT, ni código con el path tenant-scoped. |
| C | Tabla de membresías `usuario_tenant` (reemplaza el FK único) | Alto | Migra el invariante fundacional de todo el sistema para un problema que hoy solo tiene un usuario (el dueño). Sobre-ingeniería. |

## Hallazgo clave: no hace falta un rol Postgres con BYPASSRLS

`CONTEXTO.md` había anticipado que este trabajo requeriría "un rol de soporte con
`BYPASSRLS` auditado". Al revisar `schema_agrocasa_creixa.sql` esto resultó innecesario:

- `tenants` **no está** en la lista de 18 tablas con `FORCE ROW LEVEL SECURITY`
  (`schema_agrocasa_creixa.sql:349-355`) — no tiene columna `tenant_id` (es la raíz), así que
  leer/crear/activar tenants funciona con el rol `app_user` normal, sin bypass de ningún tipo.
- La única escritura que sí toca una tabla con RLS (`usuarios`, para crear el primer admin
  del tenant nuevo) se resuelve fijando `SET LOCAL app.tenant_id` al tenant recién creado
  **antes** del INSERT, dentro de la misma transacción. Eso no es un bypass — es exactamente
  el flujo normal, solo que el superadmin es quien decide a qué tenant apunta.

Esto reduce la superficie de riesgo real de esta feature por debajo de lo que el propio
proyecto había anticipado.

## Modelo de datos (nuevo)

```sql
CREATE TABLE superadmins (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(150) NOT NULL UNIQUE,
    nombre_completo VARCHAR(150) NOT NULL,
    hash_password   VARCHAR(255) NOT NULL,
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- Sin tenant_id, sin RLS -- vive fuera del boundary tenant por diseño.

CREATE TABLE superadmin_auditoria (
    id              BIGSERIAL PRIMARY KEY,
    superadmin_id   UUID NOT NULL REFERENCES superadmins(id),
    accion          VARCHAR(50) NOT NULL,   -- 'crear_tenant','activar_tenant','desactivar_tenant','impersonar'
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    detalle         JSONB,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Tabla nueva y separada de `auditoria` (no reutilizada): `auditoria.usuario_id` referencia
`usuarios(id)` y `auditoria.tenant_id` es el tenant *dueño* del evento — un superadmin no es
un `usuario` y sus acciones no pertenecen a un solo tenant en el mismo sentido. Mezclar los
dos conceptos en una tabla obligaría a debilitar esa FK o volverla ambigua.

## Autenticación

Un solo formulario de login para tenant y superadmin — decisión tomada después de la
primera pasada de este documento, a pedido del dueño ("por el mismo login que él valide
el email y clave y se dé cuenta que es el superadmin"). `POST /auth/login` (el endpoint
existente, sin URL nueva) prueba primero `usuarios`; si no hay ningún usuario de tenant con
ese email, prueba `superadmins`:

```
POST /auth/login {email, password}
  → si hay 1 usuario de tenant con ese email y la password matchea:
      JWT { sub: usuario_id, tenant_id, rol }                    -- shape de siempre
  → si NO hay ningún usuario de tenant con ese email:
      prueba superadmins; si matchea:
      JWT { sub: superadmin_id, kind: "superadmin" }              -- SIN tenant_id

get_current_superadmin (nueva dependency):
  decodifica el JWT, exige kind == "superadmin",
  busca en `superadmins` vía sesión plana (get_superadmin_db) -- no hay RLS que fijar.
```

El frontend decide a dónde aterrizar decodificando el JWT recibido (`kind === "superadmin"`
→ `/superadmin`, si no → flujo de tenant normal) — nunca antes de recibir la respuesta. Esto
además mejora la superficie de exposición: ya no existe una URL (`/superadmin/login`) que
delate que el sistema tiene un modo superadmin.

`get_current_user` (el existente, sin cambios) ya rechaza un JWT de superadmin
automáticamente: exige `tenant_id` en el payload y falla-cerrado si no está
(`app/core/deps.py:39-43`). Un token de superadmin nunca puede usarse contra un endpoint
tenant-scoped — es una propiedad del código ya existente, no algo nuevo que construir.

## Endpoints nuevos

```
POST /auth/login                            -- mismo endpoint de siempre, ahora prueba
                                                usuarios y despues superadmins (ver Autenticación)
GET  /superadmin/tenants                    -- lista todos los tenants (sin RLS)
POST /superadmin/tenants                    -- {nombre, admin_email, admin_password, admin_nombre_completo}
       transacción: INSERT tenants → SET LOCAL app.tenant_id = <nuevo id> → INSERT usuarios (rol=admin) → log auditoria
PATCH /superadmin/tenants/{id}              -- {activo: bool}
POST /superadmin/tenants/{id}/entrar        -- impersonation
```

### Impersonation

Al hacer "entrar", el backend busca el usuario `rol='admin'` **más antiguo** (`ORDER BY
creado_en ASC LIMIT 1`) dentro del tenant, y emite un JWT tenant normal (el mismo shape que
emite `/auth/login` hoy) con un claim extra `impersonated_by: <superadmin_id>`. El frontend
decodifica ese claim para mostrar un aviso ("Sesión de soporte — actuando como {tenant}");
el backend ignora el claim salvo para el log de auditoría (`get_current_user` no lo lee, así
que el resto del sistema funciona sin cambios).

## Bootstrap del primer superadmin

`backend/scripts/seed_superadmin.py`, mismo patrón que `seed_tenant.py` — nunca expuesto por
HTTP. Confirmado con el dueño: sin endpoint de arranque, sin self-service.

## Frontend

- Sin ruta de login separada: `LoginPage.tsx` (la de siempre) sirve a ambos. Su
  `handleSubmit` no cambia — solo llama `onLoginSuccess(access_token)` como ya hacía.
  `App.tsx::handleLoginSuccess` es quien decodifica el JWT y decide dónde guardarlo
  (`sistema-af.token` vs `sistema-af.superadminToken`, dos claves de `localStorage`
  separadas, cada una con su propio estado en `App.tsx`) y a qué ruta corresponde.
- Página `/superadmin` (tabla de tenants: nombre, estado, fecha de alta; acciones crear /
  activar-desactivar / entrar).
- "Entrar" guarda el JWT tenant recibido en el mismo `localStorage` key que usa el login
  normal y navega a `/dashboard` — reutiliza el `App.tsx` existente sin ningún cambio.
- Banner de "sesión de soporte" visible en `AppShell.tsx` cuando el JWT activo trae
  `impersonated_by` (decodificado client-side, sin llamada extra al backend).

## Diagrama: alta de tenant

```
Superadmin                    Backend                              DB
    │  POST /superadmin/tenants  │                                  │
    │  {nombre, admin_email, …}  │                                  │
    ├────────────────────────────►                                  │
    │                             │  BEGIN                           │
    │                             ├─── INSERT tenants ──────────────►│ (sin RLS)
    │                             │◄── tenant.id ────────────────────┤
    │                             ├─── SET LOCAL app.tenant_id ─────►│
    │                             ├─── INSERT usuarios (rol=admin) ─►│ (RLS OK: tenant_id
    │                             │                                  │  == app.tenant_id)
    │                             ├─── INSERT superadmin_auditoria ─►│
    │                             │  COMMIT                          │
    │◄─── 201 {tenant, usuario} ──┤                                  │
```

## Diagrama: impersonation

```
Superadmin                    Backend                              DB
    │ POST /superadmin/tenants/  │                                  │
    │ {id}/entrar                │                                  │
    ├────────────────────────────►                                  │
    │                             ├── SET LOCAL app.tenant_id=id ───►│
    │                             ├── SELECT usuarios WHERE rol=     │
    │                             │   'admin' ORDER BY creado_en ───►│
    │                             │   LIMIT 1                        │
    │                             │◄── usuario ───────────────────── │
    │                             ├── INSERT superadmin_auditoria ──►│
    │◄── 200 {access_token: JWT  ─┤   (impersonar)                   │
    │    tenant normal +          │                                  │
    │    impersonated_by}         │                                  │
    │                                                                 │
    │  [frontend guarda el token, navega a /dashboard --              │
    │   de acá en adelante es una sesión de tenant normal]            │
```

## Tests (backend)

`backend/tests/test_superadmin_auth.py`:
- login OK con credenciales correctas → JWT sin `tenant_id`, con `kind=superadmin`
- login rechaza password incorrecta (401)
- login rechaza email inexistente (401)
- login rechaza superadmin inactivo (401)

`backend/tests/test_superadmin_tenants_api.py`:
- `GET /superadmin/tenants` requiere JWT de superadmin (401 sin token)
- `GET /superadmin/tenants` rechaza un JWT de tenant normal (401/403 — regression test de
  que `get_current_superadmin` no acepta el shape de token equivocado)
- `POST /superadmin/tenants` crea tenant + usuario admin, devuelve 201, usuario queda con
  `tenant_id` correcto y `rol='admin'` (nota: un duplicado de `admin_email` no puede ocurrir
  aquí — la unicidad de `usuarios` es por `(tenant_id, email)` y el tenant nace vacío)
- `PATCH /superadmin/tenants/{id}` activa/desactiva correctamente
- `PATCH /superadmin/tenants/{id}` con id inexistente → 404
- `POST /superadmin/tenants/{id}/entrar` devuelve un JWT que `get_current_user` acepta
  (tenant_id presente, decodifica OK) — test de integración cruzando ambos módulos
- `POST /superadmin/tenants/{id}/entrar` en un tenant sin ningún usuario admin → 404/409
  claro (caso borde: tenant recién creado sin admin, o todos los admin desactivados)
- Cada acción mutante (crear/activar/desactivar/entrar) deja una fila en
  `superadmin_auditoria` con el `accion` y `tenant_id` correctos

## NOT in scope

- Self-service signup de superadmins — riesgo de privilegio, se descartó explícitamente.
- Elegir *qué* admin impersonar cuando hay varios — siempre el más antiguo, confirmado con
  el dueño; agregar selector es trabajo futuro si aparece la necesidad real.
- Permisos granulares entre superadmins (todos tienen el mismo poder) — no hay más de un
  superadmin real hoy; generalizar sería la misma sobre-ingeniería que descartamos en
  Approach C.
- Endpoint HTTP de bootstrap — se usa script CLI, confirmado con el dueño.
- Test automatizado de frontend (`UsuariosPage.tsx` tampoco lo tiene) — se sigue el patrón
  ya establecido en el repo: build + lint limpios, verificación manual en navegador.

## What already exists / reused

- Patrón de JWT propio (`app/core/security.py`) — mismo mecanismo, shape de token distinto.
- Patrón de endpoint admin-gated + tests (`app/api/usuarios.py`,
  `tests/test_usuarios_api.py`) — mismo estilo para `/superadmin/tenants`.
- Patrón de página admin-gated + gating de Sidebar (`UsuariosPage.tsx`, `Sidebar.tsx`,
  commits `ac9814c`/`882fd25`) — mismo estilo para la página de superadmin, salvo que esta
  vive fuera del `AppShell` normal (no hay empresa/sucursal que elegir).
- `resolverEmpresaYSucursal`/`localStorage` token pattern en `App.tsx` — reutilizado tal
  cual para aterrizar la sesión de impersonation.

## Unresolved decisions

Ninguna — ambas decisiones abiertas (bootstrap, selección de admin en impersonation) se
confirmaron con el dueño antes de escribir este documento.
