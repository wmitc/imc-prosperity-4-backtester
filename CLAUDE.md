# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`prosperity4bt` is a backtesting framework for algorithmic trading strategies written for the IMC Prosperity 4 competition. It simulates order matching against historical market data and produces output logs compatible with visualizers.

## Commands

```bash
# Install dependencies
pip install -e . --break-system-packages

# Lint
ruff check

# Type check
mypy prosperity4bt

# Run the backtester (CLI is Typer-based; use --help for full options)
python -m prosperity4bt <algorithm_file.py> <round>[-<day>] [options]

# Examples
python -m prosperity4bt example.py 0            # all days in tutorial round
python -m prosperity4bt example.py 1-0          # round 1, day 0 only
python -m prosperity4bt example.py 3 --merge-pnl
python -m prosperity4bt example.py 5 --no-out --print
```

Day specifier: `<round>` runs all days in that round; `<round>-<day>` runs one day
(negative days are written like `1--1` for round 1, day -1). Multiple day args allowed.

Key options: `--merge-pnl` (sum P&L across days), `--vis` (save per-round PNG charts to
`results/`), `--out <file>`/`--no-out` (output log path; default `backtests/<timestamp>.log`),
`--data <dir>` (custom data dir mirroring `prosperity4bt/resources/` layout), `--print`
(stream trader output), `--match-trades all|worse|none`, `--original-timestamps`,
`--no-progress`.

## Architecture

### Core Modules

**`prosperity4bt/__main__.py`** — CLI entry point (built with Typer). Dynamically imports the user's algorithm file, iterates over requested rounds/days, and writes a visualizer-compatible output log (default `backtests/<timestamp>.log`). Sets `PROSPERITY4BT_ROUND` and `PROSPERITY4BT_DAY` env vars so traders can detect the backtester context. Note: these env vars are NOT set in the official submission environment, so submitted code must not depend on them.

**`prosperity4bt/runner.py`** — The simulation engine. Key functions:
- `run_backtest()`: Main loop over timestamps; calls `trader.run(state)` each tick
- `prepare_state()`: Builds `TradingState` from price/trade CSV data
- `match_orders()`: Dispatches buy/sell orders through three-stage matching
- `match_buy_order()` / `match_sell_order()`: Match against order depth first, then market trades
- `enforce_limits()`: Cancels all orders for a product if position limits would be exceeded

**`prosperity4bt/datamodel.py`** — Domain types shared with official competition code: `TradingState`, `Order`, `OrderDepth`, `Trade`, `Observation`, etc. This file must stay compatible with the official Prosperity 4 datamodel.

**`prosperity4bt/data.py`** — CSV parsing into `BacktestData`. Contains `LIMITS` dict mapping products to position limits. `read_day_data()` loads prices, trades, and observations CSVs.

**`prosperity4bt/models.py`** — Output structures: `BacktestResult`, `SandboxLogRow`, `ActivityLogRow`, `TradeRow`. Also defines `TradeMatchingMode` enum (`all` / `worse` / `none`).

**`prosperity4bt/file_reader.py`** — Pluggable data source abstraction. `FileSystemReader` reads from disk; `PackageResourcesReader` reads bundled package data.

**`prosperity4bt/parse_submission_logs.py`** — Utility to convert official submission environment output logs into the CSV format used by this backtester.

**`prosperity4bt/visualize.py`** — `--vis` handler. Renders per-round PNG charts (mid price + P&L per product) to `results/`, stitching multiple days into one continuous x-axis. Skips one-sided-book rows where `mid == 0`.

**`prosperity4bt/open.py`** — Serves an output log over a one-shot localhost HTTP server and opens it in the jmerle Prosperity visualizer web app in the browser.

### Strategy Files

Root-level `*_strategy.py` (e.g. `round3_strategy.py`, `tutorial_strategy.py`) are the user's actual trading algorithms — one per round. Each defines a `Trader` class with a `run(state)` method. `example.py` is a minimal reference trader. These are the files passed as the `<algorithm_file.py>` argument.

### Data Flow

1. Load the user's algorithm file and extract the `Trader` class
2. For each requested round/day, call `read_day_data()` to load CSVs
3. Per-timestamp loop:
   - `prepare_state()` builds `TradingState` with order depths and empty observations
   - Call `trader.run(state)` to get orders and conversions
   - `enforce_limits()` cancels orders that would exceed position limits
   - `match_orders()` fills orders against order depth (priority), then market trades
   - Update positions and P&L, record activity log snapshots
4. Merge results across days and write JSON output

### Order Matching Details

Three-stage matching per order:
1. **Order depth**: Fill against available volume at prices equal to or better than the order price
2. **Market trades** (if `--match-trades` is not `none`):
   - `all` mode (default): match trades at prices equal to or better than the order
   - `worse` mode: match only at worse prices
3. Orders are filled at the **order's own price**, not the market trade price.

Position limits are enforced before matching — if any order would exceed the limit, **all** orders for that product are cancelled.

## Products and Position Limits

| Round | Products | Limit |
|-------|----------|-------|
| 0 (tutorial) | EMERALDS, TOMATOES | 80 |
| 1–2 | ASH_COATED_OSMIUM, INTARIAN_PEPPER_ROOT | 80 |
| 3–4 | HYDROGEL_PACK, VELVETFRUIT_EXTRACT | 200 |
| 3–4 | VEV_4000/4500/5000/5100/5200/5300/5400/5500/6000/6500 | 300 |
| 5 | 50 products (GALAXY_SOUNDS_\*, MICROCHIP_\*, OXYGEN_SHAKE_\*, PANEL_\*, PEBBLES_\*, ROBOT_\*, SLEEP_POD_\*, SNACKPACK_\*, TRANSLATOR_\*, UV_VISOR_\*) | 10 |

## Adding New Products / Rounds

- Add position limits to `LIMITS` in `prosperity4bt/data.py`
- Add CSV data files under `prosperity4bt/resources/round<r>/` following the naming convention `prices_round_<r>_day_<d>.csv`, `trades_round_<r>_day_<d>.csv`, and optionally `observations_round_<r>_day_<d>.csv`
- Note the delimiter split: prices and trades CSVs are **`;`-delimited**; observations CSVs are **`,`-delimited** (see `read_day_data()` in `data.py`)
