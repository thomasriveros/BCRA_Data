# BCRA monetary data CSV

This repository downloads the 35 indicators that the Banco Central de la República Argentina (BCRA) officially classifies as **Principales Variables** and stores their complete histories in one analysis-ready CSV. This keeps the output focused on reserves, exchange rates, inflation, interest rates, monetary aggregates, deposits, loans, and indexed units.

## Output

`data/bcra_monetary.csv` uses long format and is sorted by `id_variable`, then `fecha`:

| Column | Meaning |
|---|---|
| `id_variable` | Stable BCRA variable identifier |
| `fecha` | Observation date (`YYYY-MM-DD`) |
| `valor` | Published value |
| `descripcion` | Variable name |
| `categoria` | BCRA category |
| `tipo_serie` | Economic series type |
| `periodicidad` | `D` daily, `M` monthly, `T`/`Q` quarterly |
| `unidad_expresion` | Unit of measure |
| `moneda` | BCRA currency classification |

## Automatic updates

The GitHub Actions workflow runs every day at 11:25 UTC and can also be started manually. The first run downloads full history for the important-variable category. Later runs re-fetch the most recent 31 days for each variable so revisions are captured, merge by `(id_variable, fecha)`, and commit only real changes. Forward-looking values (such as exchange-band paths) are preserved without allowing future dates to break the refresh window.

The workflow needs no API key. Repository Actions must have **Read and write permissions** under **Settings → Actions → General → Workflow permissions**.

## Run locally

Python 3.11+ is sufficient; there are no third-party dependencies.

```bash
python src/pull_bcra.py
```

To change the scope, pass another official category, choose IDs explicitly, or download the full 1,581-variable catalog:

```bash
python src/pull_bcra.py --category "Principales Variables"
python src/pull_bcra.py --ids 1,4,5,15,27,28
python src/pull_bcra.py --all-variables
```

For a quick check:

```bash
python src/pull_bcra.py --ids 1,4 --output /tmp/bcra_smoke.csv
```

Source: [BCRA Monetary Statistics API v4 documentation](https://www.bcra.gob.ar/archivos/Catalogo/Content/files/pdf/principales-variables-v4.pdf).
