import csv
import tempfile
import unittest
from datetime import date
from pathlib import Path

from src.build_catalog import CATALOG_FIELDS, build_catalog, write_catalog_csv_atomic
from src.pull_all_variables import normalize_catalog
from src.pull_bcra import FIELDS, load_existing, write_csv_atomic


class CsvTests(unittest.TestCase):
    def test_round_trip_and_latest_date(self):
        row = dict.fromkeys(FIELDS, "")
        row.update({"id_variable": "7", "fecha": "2026-07-18", "valor": "123.45"})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.csv"
            write_csv_atomic(path, {(7, "2026-07-18"): row})
            rows, latest = load_existing(path)
            self.assertEqual(rows[(7, "2026-07-18")]["valor"], "123.45")
            self.assertEqual(latest[7], date(2026, 7, 18))
            with path.open(encoding="utf-8") as handle:
                self.assertEqual(next(csv.reader(handle)), FIELDS)

    def test_catalog_csv_is_sorted_and_summarized(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "observations.csv"
            output = Path(directory) / "catalog.csv"
            rows = [
                dict.fromkeys(FIELDS, ""),
                dict.fromkeys(FIELDS, ""),
                dict.fromkeys(FIELDS, ""),
            ]
            rows[0].update(
                {
                    "id_variable": "15",
                    "fecha": "2026-07-22",
                    "valor": "1",
                    "descripcion": "Base monetaria",
                    "categoria": "Principales Variables",
                    "tipo_serie": "Saldos",
                    "periodicidad": "D",
                    "unidad_expresion": "En millones de ARS",
                    "moneda": "ML",
                }
            )
            rows[1].update(
                {
                    "id_variable": "1",
                    "fecha": "2026-07-22",
                    "valor": "2",
                    "descripcion": "Reservas internacionales",
                    "categoria": "Principales Variables",
                    "tipo_serie": "Saldos",
                    "periodicidad": "D",
                    "unidad_expresion": "En millones de USD",
                    "moneda": "ME",
                }
            )
            rows[2].update(rows[1])
            rows[2].update({"fecha": "1996-01-03", "valor": "3"})
            with source.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerows(rows)
            catalog = build_catalog(source)
            write_catalog_csv_atomic(output, catalog)
            with output.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(list(rows[0]), CATALOG_FIELDS)
            self.assertEqual([row["id_variable"] for row in rows], ["1", "15"])
            self.assertEqual(rows[0]["descripcion"], "Reservas internacionales")
            self.assertEqual(rows[0]["primer_fecha_informada"], "1996-01-03")
            self.assertEqual(rows[0]["ultima_fecha_informada"], "2026-07-22")
            self.assertEqual(rows[0]["ultimo_valor_informado"], "2")

    def test_complete_api_catalog_is_normalized_and_sorted(self):
        variables = [
            {
                "idVariable": 15,
                "descripcion": "Base monetaria",
                "categoria": "Principales Variables",
                "tipoSerie": "Saldos",
                "periodicidad": "D",
                "unidadExpresion": "En millones de ARS",
                "moneda": "ML",
                "primerFechaInformada": "1990-01-01",
                "ultFechaInformada": "2026-07-22",
                "ultValorInformado": 123.45,
            },
            {
                "idVariable": 1,
                "descripcion": "Reservas internacionales",
                "categoria": "Principales Variables",
            },
        ]
        rows = normalize_catalog(variables)
        self.assertEqual([row["id_variable"] for row in rows], ["1", "15"])
        self.assertEqual(list(rows[0]), CATALOG_FIELDS)
        self.assertEqual(rows[0]["periodicidad"], "")
        self.assertEqual(rows[1]["ultimo_valor_informado"], "123.45")


if __name__ == "__main__":
    unittest.main()
