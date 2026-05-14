# IMC Prosperity 4 Backtester

A backtester for [IMC Prosperity 4](https://prosperity.imc.com/) trading algorithms. Simulates order matching against historical market data and produces output logs compatible with standard Prosperity visualizers.

## Installation

```sh
pip install -e . --break-system-packages
```

## Usage

```sh
# Run on all days in the tutorial round (round 0)
python -m prosperity4bt <algorithm.py> 0

# Run on a specific day (round 1, day -1)
python -m prosperity4bt <algorithm.py> 1--1

# Run on all days in round 3
python -m prosperity4bt <algorithm.py> 3

# Merge profit and loss across days
python -m prosperity4bt <algorithm.py> 1 --merge-pnl

# Save per-round PNG charts to results/
python -m prosperity4bt <algorithm.py> 1 --vis

# Skip saving the output log
python -m prosperity4bt <algorithm.py> 1 --no-out

# Print trader output to stdout while running (useful for debugging)
python -m prosperity4bt <algorithm.py> 1 --print

# Backtest on custom data directory
python -m prosperity4bt <algorithm.py> 1 --data path/to/data
```

## Order Matching

Orders placed by `Trader.run` at a given timestamp are matched in two stages:

1. **Order depth** — filled against the available volume at equal or better prices in the order book.
2. **Market trades** — any remaining quantity is matched against that timestamp's market trades. Fills happen at *your* order price, not the market trade price (e.g. a sell order at 9 matched against a 10 trade fills at 9).

Limits are enforced before matching. If any order for a product would push the position beyond its limit, all orders for that product are cancelled.

The `--match-trades` option controls market trade matching:
- `all` (default): match trades at prices equal to or better than your quotes.
- `worse`: match only trades at prices strictly better than your quotes.
- `none`: disable market trade matching entirely.

## Data

Data is included for rounds 0–5:

| Round | Days | Products |
|-------|------|----------|
| 0 (tutorial) | -2, -1 | EMERALDS, TOMATOES |
| 1 | -2, -1, 0 | ASH_COATED_OSMIUM, INTARIAN_PEPPER_ROOT |
| 2 | -1, 0, 1 | ASH_COATED_OSMIUM, INTARIAN_PEPPER_ROOT |
| 3 | 0, 1, 2 | HYDROGEL_PACK, VELVETFRUIT_EXTRACT, VEV_4000/4500/5000/5100/5200/5300/5400/5500/6000/6500 |
| 4 | 1, 2, 3 | HYDROGEL_PACK, VELVETFRUIT_EXTRACT, VEV_4000/4500/5000/5100/5200/5300/5400/5500/6000/6500 |
| 5 | 2, 3, 4 | 50 products across GALAXY_SOUNDS, MICROCHIP, OXYGEN_SHAKE, PANEL, PEBBLES, ROBOT, SLEEP_POD, SNACKPACK, TRANSLATOR, UV_VISOR families |

## Environment Variables

Two environment variables are set during backtests so traders can detect the context:

- `PROSPERITY4BT_ROUND` — the current round number
- `PROSPERITY4BT_DAY` — the current day number

These are not present in the official submission environment, so don't depend on them in submitted code.

## Development

```sh
# Clone the repo and install in editable mode
pip install -e . --break-system-packages

# Lint
ruff check

# Type check
mypy prosperity4bt
```
