import csv
import uuid
from unittest.mock import MagicMock, patch

from scripts.import_plan_cuentas import main


def _write_csv(tmp_path, rows):
    csv_path = tmp_path / "catalogo.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["numero_cta", "nivel", "tipo_cta", "nombre"])
        writer.writeheader()
        writer.writerows(rows)
    return csv_path


def test_import_inserts_one_plancuenta_per_row(tmp_path, monkeypatch):
    tenant_id = uuid.uuid4()
    csv_path = _write_csv(
        tmp_path,
        [
            {"numero_cta": "10000000", "nivel": "1", "tipo_cta": "1", "nombre": "Activos"},
            {"numero_cta": "20000000", "nivel": "1", "tipo_cta": "2", "nombre": "Pasivos"},
        ],
    )

    fake_db = MagicMock()
    with patch("scripts.import_plan_cuentas.SessionLocal", return_value=fake_db):
        monkeypatch.setattr(
            "sys.argv",
            ["import_plan_cuentas", "--tenant-id", str(tenant_id), "--csv", str(csv_path)],
        )
        main()

    assert fake_db.add.call_count == 2
    first_cuenta = fake_db.add.call_args_list[0].args[0]
    assert first_cuenta.numero_cta == "10000000"
    assert first_cuenta.tenant_id == tenant_id
    assert first_cuenta.nivel == 1
    fake_db.commit.assert_called_once()
    fake_db.close.assert_called_once()


def test_import_strips_whitespace_from_numero_cta_and_nombre(tmp_path, monkeypatch):
    tenant_id = uuid.uuid4()
    csv_path = _write_csv(
        tmp_path,
        [{"numero_cta": " 10000000 ", "nivel": "1", "tipo_cta": "1", "nombre": " Activos "}],
    )

    fake_db = MagicMock()
    with patch("scripts.import_plan_cuentas.SessionLocal", return_value=fake_db):
        monkeypatch.setattr(
            "sys.argv",
            ["import_plan_cuentas", "--tenant-id", str(tenant_id), "--csv", str(csv_path)],
        )
        main()

    cuenta = fake_db.add.call_args_list[0].args[0]
    assert cuenta.numero_cta == "10000000"
    assert cuenta.nombre == "Activos"
