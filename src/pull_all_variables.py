#!/usr/bin/env python3
"""Download the complete BCRA monetary-variable catalog into a CSV."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

try:
    from src.build_catalog import write_catalog_csv_atomic
    from src.pull_bcra import fetch_catalog
except ModuleNotFoundError:
    from build_catalog import write_catalog_csv_atomic
    from pull_bcra import fetch_catalog


def normalize_catalog(variables: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows = []
    for variable in variables:
        rows.append(
            {
                "id_variable": str(variable.get("idVariable", "")),
                "descripcion": str(variable.get("descripcion", "")),
                "categoria": str(variable.get("categoria", "")),
                "tipo_serie": str(variable.get("tipoSerie", "")),
                "periodicidad": str(variable.get("periodicidad", "")),
                "unidad_expresion": str(variable.get("unidadExpresion", "")),
                "moneda": str(variable.get("moneda", "")),
                "primer_fecha_informada": str(variable.get("primerFechaInformada", "")),
                "ultima_fecha_informada": str(variable.get("ultFechaInformada", "")),
                "ultimo_valor_informado": str(variable.get("ultValorInformado", "")),
            }
        )
    return sorted(rows, key=lambda row: int(row["id_variable"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/bcra_all_variables.csv"))
    args = parser.parse_args()
    rows = normalize_catalog(fetch_catalog())
    write_catalog_csv_atomic(args.output, rows)
    print(f"Wrote {len(rows)} variables to {args.output}")


if __name__ == "__main__":
    main()
