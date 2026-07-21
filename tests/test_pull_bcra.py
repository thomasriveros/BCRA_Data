import csv
import tempfile
import unittest
from datetime import date
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
