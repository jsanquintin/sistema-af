"""Importa el catalogo de cuentas (CSV exportado de Soluflex) a plan_cuentas.

Carga de staging, no numeracion final -- ver Open Question 5 en
docs/designs/nucleo-contabilidad-nomina.md: si Creixa termina necesitando
su propia numeracion, este catalogo puede requerir dividirse o renumerarse
antes de considerarse definitivo. No reinterpreta la jerarquia del CSV,
la carga tal cual (decision ya tomada en CONTEXTO.md).

Uso:
    python -m scripts.import_plan_cuentas --tenant-id <uuid> --csv ../catalogo_cuentas_agrocasa.csv
"""
import argparse
import csv
import uuid
from pathlib import Path

from app.db.session import SessionLocal
from app.models.plan_cuenta import PlanCuenta


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", required=True, type=uuid.UUID)
    parser.add_argument("--csv", required=True, type=Path)
    args = parser.parse_args()

    with args.csv.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    db = SessionLocal()
    try:
        insertadas = 0
        for row in rows:
            cuenta = PlanCuenta(
                tenant_id=args.tenant_id,
                numero_cta=row["numero_cta"].strip(),
                nivel=int(row["nivel"]),
                tipo_cta=int(row["tipo_cta"]),
                nombre=row["nombre"].strip(),
                activo=True,
            )
            db.add(cuenta)
            insertadas += 1
        db.commit()
        print(f"{insertadas} cuentas importadas para tenant {args.tenant_id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
