# sistema-af

Reemplazo de Soluflex para Agrocasa (agroexportación café/cacao) y Creixa
(inversiones), construido como SaaS multi-tenant (cada tenant es un cliente
del sistema; Agrocasa/Creixa comparten un tenant como dos empresas del mismo
grupo). Contexto completo del proyecto en [CONTEXTO.md](CONTEXTO.md) — léelo
antes de tocar el esquema o el modelo de nómina.

**Stack:** FastAPI + PostgreSQL 16 (RLS) · React + Vite + TypeScript +
Tailwind + shadcn/ui.

## Antes de escribir lógica de negocio (asientos, nómina)

Hay un gate documentado en [docs/designs/nucleo-contabilidad-nomina.md](docs/designs/nucleo-contabilidad-nomina.md)
("The Assignment"): no se construye el motor de asientos ni de nómina hasta
resolver 7 incógnitas con el contador interno y confirmar el estatus de e-CF
ante la DGII. Todo lo demás (skeleton, auth, catálogo de cuentas, seguridad
multi-tenant) ya está construido y no depende de esas respuestas.

## Requisitos

- Python 3.13+
- Node.js 20+
- PostgreSQL 16 — local vía Docker, o remoto (Railway, etc.)

## Setup del backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # .venv/bin/pip en Linux/Mac
cp .env.example .env
```

Edita `.env`:
- `DATABASE_URL` — conexión de **owner/admin** (migraciones, scripts). Con
  Docker local: `docker compose up -d db` desde la raíz del repo, usa las
  credenciales de `docker-compose.yml`. Con Railway: `railway variables`
  después de `railway add --database postgres`.
- `JWT_SECRET_KEY` — generar uno real, nunca usar el placeholder:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(48))"
  ```
- `APP_DATABASE_URL` — se completa en el siguiente paso.

Correr la migración (crea las 19 tablas + RLS + trigger de cuadre) y el rol
de runtime:

```bash
.venv/Scripts/alembic upgrade head
.venv/Scripts/python -m scripts.setup_app_role --password "una-contraseña-fuerte"
```

Ahora sí completa `APP_DATABASE_URL` en `.env` con el usuario `app_user` y
esa contraseña (mismo host/puerto/DB que `DATABASE_URL`). Esta es la conexión
con la que corre el backend en runtime — RLS la restringe de verdad, a
diferencia de la conexión de owner.

Sembrar el primer tenant + usuario admin, e importar el catálogo de cuentas
(carga de staging, ver Open Question 5 en el design doc — puede necesitar
renumerarse si Creixa termina con su propio catálogo):

```bash
.venv/Scripts/python -m scripts.seed_tenant --nombre "Agrocasa/Creixa" --email admin@agrocasa.com --password "cambia-esto"
.venv/Scripts/python -m scripts.import_plan_cuentas --tenant-id <uuid-que-imprimió-seed_tenant> --csv ../catalogo_cuentas_agrocasa.csv
```

Correr tests y levantar el servidor:

```bash
.venv/Scripts/pytest tests/ -v
.venv/Scripts/uvicorn app.main:app --reload
```

## Setup del frontend

```bash
cd frontend
npm install
npm run dev
```

Por defecto apunta a `http://localhost:8000` (el backend). Para cambiarlo,
define `VITE_API_URL` en `frontend/.env.local`.

## Estructura del repo

```
backend/
  app/
    api/        endpoints (auth, plan_cuentas)
    core/       config, seguridad (JWT/argon2), dependencias de FastAPI
    db/         conexión (dos engines: owner y app_user), Base declarativa
    models/     modelos SQLAlchemy, reflejan el schema tal cual
    schemas/    modelos Pydantic (request/response)
  alembic/      migraciones (0001 versiona el schema completo, 0002+ son incrementales)
  scripts/      operaciones de admin (seed, import, setup de roles) -- no son endpoints
  tests/
frontend/
  src/
    pages/      pantallas (LoginPage)
    components/ui/  componentes shadcn
    lib/        cliente de API
docs/designs/   design docs de /office-hours + /plan-eng-review (gstack)
```

## Seguridad multi-tenant

El backend usa **dos conexiones distintas** a la base (ver `app/db/session.py`):
- `SessionLocal` (owner): Alembic, scripts de admin, y el lookup de usuario
  en login (necesita ver todos los tenants antes de saber a cuál pertenece
  quien inicia sesión — no hay forma de evitar esto sin conocer el tenant
  de antemano).
- `AppSessionLocal` (rol `app_user`, sin privilegios de owner): todo lo
  demás. `get_tenant_db` (en `app/core/deps.py`) fija `app.tenant_id` antes
  de cualquier query de negocio, fail-closed — si el JWT no trae un tenant
  válido, no hay fallback a un tenant por defecto.

Ver el checklist completo (pgbouncer, rol de soporte `BYPASSRLS` auditado —
diferidos hasta que exista un segundo tenant real) en [CONTEXTO.md](CONTEXTO.md)
y [TODOS.md](TODOS.md).
