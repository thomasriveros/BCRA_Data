#!/usr/bin/env python3
"""Download every BCRA monetary variable into one deterministic CSV."""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "https://api.bcra.gob.ar/estadisticas/v4.0"
FIELDS = [
    "id_variable",
    "fecha",
    "valor",
    "descripcion",
    "categoria",
    "tipo_serie",
    "periodicidad",
    "unidad_expresion",
    "moneda",
]


def api_get(path: str, params: dict[str, Any] | None = None, retries: int = 6) -> dict[str, Any]:
    url = f"{BASE_URL}/{path}"
    if params:
        url += "?" + urlencode(params)
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "Accept-Language": "es-AR",
            "User-Agent": "github.com/bcra-data-csv updater",
        },
    )
    for attempt in range(retries):
        try:
            with urlopen(request, timeout=90) as response:
                payload = json.load(response)
            if payload.get("status") != 200:
                raise RuntimeError(f"BCRA returned status {payload.get('status')}: {payload}")
            return payload
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
            if attempt == retries - 1:
                raise RuntimeError(f"Request failed after {retries} attempts: {url}") from exc
            time.sleep(min(30, 2**attempt) + random.random())
    raise AssertionError("unreachable")


def fetch_catalog(category: str | None = None) -> list[dict[str, Any]]:
    variables: list[dict[str, Any]] = []
    offset = 0
    limit = 1000
    while True:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if category:
            params["categoria"] = category
        payload = api_get("monetarias", params)
        variables.extend(payload.get("results", []))
        total = int(payload["metadata"]["resultset"]["count"])
        offset += len(payload.get("results", []))
        if offset >= total:
            break
        if not payload.get("results"):
            raise RuntimeError("Catalog pagination stopped before reaching the reported total")
    return variables


def fetch_observations(variable: dict[str, Any], start: str | None) -> list[dict[str, str]]:
    variable_id = int(variable["idVariable"])
    offset = 0
    limit = 3000
    rows: list[dict[str, str]] = []
    while True:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if start:
            params["desde"] = start
        payload = api_get(f"monetarias/{variable_id}", params)
        results = payload.get("results", [])
        detail = results[0].get("detalle", []) if results else []
        for item in detail:
            rows.append(
                {
                    "id_variable": str(variable_id),
                    "fecha": str(item["fecha"]),
                    "valor": str(item["valor"]),
                    "descripcion": str(variable.get("descripcion", "")),
                    "categoria": str(variable.get("categoria", "")),
                    "tipo_serie": str(variable.get("tipoSerie", "")),
                    "periodicidad": str(variable.get("periodicidad", "")),
                    "unidad_expresion": str(variable.get("unidadExpresion", "")),
                    "moneda": str(variable.get("moneda", "")),
                }
            )
        total = int(payload.get("metadata", {}).get("resultset", {}).get("count", len(detail)))
        offset += len(detail)
        if offset >= total:
            break
        if not detail:
            raise RuntimeError(f"Variable {variable_id} pagination stopped at {offset}/{total}")
    return rows


def load_existing(path: Path) -> tuple[dict[tuple[int, str], dict[str, str]], dict[int, date]]:
    rows: dict[tuple[int, str], dict[str, str]] = {}
    latest: dict[int, date] = {}
    if not path.exists():
        return rows, latest
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            variable_id = int(row["id_variable"])
            observation_date = date.fromisoformat(row["fecha"])
            rows[(variable_id, row["fecha"])] = row
            latest[variable_id] = max(latest.get(variable_id, date.min), observation_date)
    return rows, latest


def write_csv_atomic(path: Path, rows: dict[tuple[int, str], dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", dir=path.parent, delete=False) as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for key in sorted(rows):
            writer.writerow(rows[key])
        temporary = Path(handle.name)
    os.replace(temporary, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/bcra_monetary.csv"))
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--lookback-days", type=int, default=31)
    parser.add_argument(
        "--category",
        default="Principales Variables",
        help="BCRA category to publish (default: Principales Variables)",
    )
    parser.add_argument(
        "--all-variables",
        action="store_true",
        help="Publish all API variables instead of the selected category",
    )
    parser.add_argument("--ids", help="Comma-separated IDs for a targeted run")
    parser.add_argument("--max-variables", type=int, help="Limit variables for a smoke test")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    existing, latest = load_existing(args.output)
    catalog = fetch_catalog(None if args.all_variables else args.category)
    if args.ids:
        wanted = {int(value) for value in args.ids.split(",")}
        catalog = [variable for variable in catalog if int(variable["idVariable"]) in wanted]
    if args.max_variables is not None:
        catalog = catalog[: args.max_variables]

    def task(variable: dict[str, Any]) -> tuple[int, str | None, list[dict[str, str]]]:
        variable_id = int(variable["idVariable"])
        start = None
        if variable_id in latest:
            # Some BCRA series contain forward-looking observations. Never anchor
            # the revision window in the future because the API rejects it.
            anchor = min(latest[variable_id], date.today())
            start = (anchor - timedelta(days=args.lookback_days)).isoformat()
        return variable_id, start, fetch_observations(variable, start)

    completed = 0
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(task, variable): variable for variable in catalog}
        for future in as_completed(futures):
            variable_id, start, new_rows = future.result()
            if start:
                for key in [key for key in existing if key[0] == variable_id and key[1] >= start]:
                    del existing[key]
            for row in new_rows:
                existing[(variable_id, row["fecha"])] = row
            completed += 1
            if completed % 50 == 0 or completed == len(catalog):
                print(f"Fetched {completed}/{len(catalog)} variables", flush=True)

    write_csv_atomic(args.output, existing)
    print(f"Wrote {len(existing):,} observations to {args.output}")


if __name__ == "__main__":
    main()
