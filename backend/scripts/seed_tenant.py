"""Crea el primer tenant + usuario admin para desarrollo local.

No es un endpoint publico a proposito (ver checklist de aprovisionamiento
en CONTEXTO.md: "script/endpoint admin para dar de alta un tenant nuevo"
todavia no se ha construido como endpoint). Uso:

    python -m scripts.seed_tenant --nombre "Agrocasa/Creixa" --email admin@agrocasa.com --password "..."
"""
import argparse
import uuid

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.tenant import Tenant
from app.models.usuario import Usuario


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nombre", required=True, help="Nombre del tenant (ej. 'Agrocasa/Creixa')")
    parser.add_argument("--email", required=True, help="Email del primer usuario admin")
    parser.add_argument("--password", required=True, help="Password del primer usuario admin")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        tenant = Tenant(id=uuid.uuid4(), nombre=args.nombre, activo=True)
        db.add(tenant)
        db.flush()

        usuario = Usuario(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            empresa_id=None,
            email=args.email,
            nombre_completo=args.email,
            hash_password=hash_password(args.password),
            rol="admin",
            activo=True,
        )
        db.add(usuario)
        db.commit()

        print(f"Tenant creado: {tenant.id} ({tenant.nombre})")
        print(f"Usuario admin creado: {usuario.id} ({usuario.email})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
