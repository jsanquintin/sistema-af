"""Crea la primera cuenta de superadmin.

No es un endpoint publico a proposito -- el rol de superadmin cruza
tenants, asi que no tiene alta self-service (ver
docs/designs/panel-superadmin-multitenant.md). Uso:

    python -m scripts.seed_superadmin --email admin@tuempresa.com --password "..."
"""
import argparse
import uuid

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.superadmin import Superadmin


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True, help="Email del superadmin")
    parser.add_argument("--nombre", default=None, help="Nombre completo (por defecto, el email)")
    parser.add_argument("--password", required=True, help="Password del superadmin")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        superadmin = Superadmin(
            id=uuid.uuid4(),
            email=args.email,
            nombre_completo=args.nombre or args.email,
            hash_password=hash_password(args.password),
            activo=True,
        )
        db.add(superadmin)
        db.commit()

        print(f"Superadmin creado: {superadmin.id} ({superadmin.email})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
