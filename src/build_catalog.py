#!/usr/bin/env python3
"""Build a one-row-per-variable catalog from the published BCRA observations."""

from __future__ import annotations

import argparse
import csv
import os
import tempfile
from pathlib import Path


CATALOG_FIELDS = [
    "id_variable",
    "descripcion",
    "categoria",
    "tipo_serie",
    "periodicidad",
    "unidad_expresion",
    "moneda",
    "primer_fecha_informada",
    "ultima_fecha_informada",
    "ultimo_valor_informado",
]


def build_catalog(source: Path) -> list[dict[str, str]]:
    variables: dict[int, dict[str, str]] = {}
    with source.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            variable_id = int(row["id_variable"])
            if variable_id not in variables:
                variables[variable_id] = {
                    "id_variable": str(variable_id),
                    "descripcion": row["descripcion"],
                    "categoria": row["categoria"],
                    "tipo_serie": row["tipo_serie"],
                    "periodicidad": row["periodicidad"],
                    "unidad_expresion": row["unidad_expresion"],
                    "moneda": row["moneda"],
                    "primer_fecha_informada": row["fecha"],
                    "ultima_fecha_informada": row["fecha"],
                    "ultimo_valor_informado": row["valor"],
                }
            else:
                current = variables[variable_id]
                if row["fecha"] < current["primer_fecha_informada"]:
                    current["primer_fecha_informada"] = row["fecha"]
                if row["fecha"] >= current["ultima_fecha_informada"]:
                    current["ultima_fecha_informada"] = row["fecha"]
                    current["ultimo_valor_informado"] = row["valor"]
    return [variables[key] for key in sorted(variables)]


def write_catalog_csv_atomic(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", newline="", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=CATALOG_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("data/bcra_monetary.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/bcra_variables.csv"))
    args = parser.parse_args()
    rows = build_catalog(args.source)
    write_catalog_csv_atomic(args.output, rows)
    print(f"Wrote {len(rows)} variables to {args.output}")


if __name__ == "__main__":
    main()
