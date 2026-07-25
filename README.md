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

`data/bcra_variables.csv` is the compact variable catalog. It contains one row per available principal variable, including the BCRA ID, description, category, series type, frequency, unit, currency, coverage dates, and latest published value.

## Available principal variables

The default dataset contains the following 35 variables from the BCRA **Principales Variables** category:

| ID | Variable | Frequency |
|---:|---|:---:|
| 1 | Reservas internacionales | D |
| 4 | Tipo de cambio minorista (promedio vendedor) | D |
| 5 | Tipo de cambio mayorista de referencia | D |
| 7 | Tasa de interés BADLAR de bancos privados — nominal anual | D |
| 8 | Tasa de interés TM20 de bancos privados | D |
| 11 | Tasa de préstamos entre entidades financieras privadas (BAIBAR) | D |
| 12 | Tasa de depósitos a 30 días de plazo | D |
| 13 | Tasa de adelantos en cuenta corriente | D |
| 14 | Tasa de préstamos personales | D |
| 15 | Base monetaria | D |
| 16 | Circulación monetaria | D |
| 17 | Billetes y monedas en poder del público | D |
| 18 | Efectivo en entidades financieras | D |
| 19 | Depósitos de entidades financieras en cuenta corriente en el BCRA | D |
| 21 | Depósitos en efectivo en las entidades financieras | D |
| 22 | Depósitos en cuentas corrientes, netos de utilización FUCO | D |
| 23 | Depósitos en cajas de ahorro | D |
| 24 | Depósitos a plazo, incluidas inversiones y excluidos CEDROs | D |
| 25 | Variación interanual del promedio móvil de 30 días del M2 privado | D |
| 26 | Préstamos de las entidades financieras al sector privado | D |
| 27 | Inflación mensual | M |
| 28 | Inflación interanual | M |
| 29 | Mediana de inflación esperada para los próximos 12 meses | M |
| 30 | Coeficiente de Estabilización de Referencia (CER) | D |
| 31 | Unidad de Valor Adquisitivo (UVA) | D |
| 32 | Unidad de Vivienda (UVI) | D |
| 35 | Tasa BADLAR de bancos privados — efectiva anual | D |
| 40 | Índice para Contratos de Locación (ICL) | D |
| 43 | Tasa de interés del Comunicado P 14.290 (uso de justicia) | D |
| 44 | Tasa TAMAR de bancos privados — nominal anual | D |
| 45 | Tasa TAMAR de bancos privados — efectiva anual | D |
| 1187 | Régimen de bandas cambiarias — límite inferior | D |
| 1188 | Régimen de bandas cambiarias — límite superior | D |
| 1197 | Tasa de Intereses Moratorios (TIM), CCC art. 768(c) | D |
| 1198 | Tasa pasiva, Ley 27.802 art. 55(a) | D |

`D` means daily and `M` means monthly. The catalog CSV is the authoritative machine-readable list and is refreshed by the same daily workflow as the observation data.

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
