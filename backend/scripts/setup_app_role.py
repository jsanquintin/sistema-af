"""Crea el rol app_user y le da los permisos minimos que necesita.

app_user es el rol con el que corre el backend en runtime -- deliberadamente
NO es el owner de las tablas, para que FORCE ROW LEVEL SECURITY (ya activo
en el schema) realmente lo restrinja. Ver CONTEXTO.md, checklist de
seguridad multi-tenant, puntos A y C.

Se conecta con DATABASE_URL (el owner/admin), no con APP_DATABASE_URL.
Idempotente: se puede correr varias veces sin duplicar el rol ni los grants.

Uso:
    python -m scripts.setup_app_role --password "una-contrasena-fuerte"
"""
import argparse

from sqlalchemy import text

from app.db.session import engine


def _sql_string_literal(value: str) -> str:
    # Escapado estandar de Postgres para literales '...': duplicar comillas
    # simples. Suficiente porque standard_conforming_strings viene en ON
    # por defecto desde Postgres 9.1 (backslash no es especial aqui).
    return "'" + value.replace("'", "''") + "'"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--password", required=True, help="Password para el rol app_user")
    args = parser.parse_args()

    password_literal = _sql_string_literal(args.password)

    with engine.begin() as conn:
        ya_existe = conn.execute(
            text("SELECT 1 FROM pg_roles WHERE rolname = 'app_user'")
        ).scalar()

        if ya_existe:
            conn.execute(text(f"ALTER ROLE app_user LOGIN PASSWORD {password_literal}"))
        else:
            conn.execute(text(f"CREATE ROLE app_user LOGIN PASSWORD {password_literal}"))

        conn.execute(text("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user"))
        conn.execute(text("GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO app_user"))
        # Para que las tablas/secuencias que agreguen migraciones futuras ya
        # vengan con el grant puesto, sin tener que recordar correr esto de
        # nuevo cada vez que se agrega una tabla.
        conn.execute(
            text(
                "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
                "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user"
            )
        )
        conn.execute(
            text(
                "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
                "GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO app_user"
            )
        )

    print(f"Rol app_user {'actualizado' if ya_existe else 'creado'} con los permisos correctos.")


if __name__ == "__main__":
    main()
