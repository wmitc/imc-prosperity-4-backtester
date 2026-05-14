from collections import defaultdict
from itertools import groupby
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt

from prosperity4bt.models import BacktestResult

matplotlib.use("Agg")


def save_visualizations(results: list[BacktestResult], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Group per-day results by round number
    by_round: dict[int, list[BacktestResult]] = defaultdict(list)
    for r in results:
        by_round[r.round_num].append(r)

    saved = []
    for round_num, round_results in sorted(by_round.items()):
        # Collect activity log rows for all days in this round
        prices: dict[str, list[float]] = defaultdict(list)
        pnls: dict[str, list[float]] = defaultdict(list)
        timestamps: dict[str, list[int]] = defaultdict(list)

        # Use a running timestamp offset so merged days form a continuous x-axis
        ts_offset = 0
        for day_result in round_results:
            day_timestamps: dict[str, list[int]] = defaultdict(list)
            day_prices: dict[str, list[float]] = defaultdict(list)
            day_pnls: dict[str, list[float]] = defaultdict(list)

            for row in day_result.activity_logs:
                product = row.columns[2]
                day_timestamps[product].append(row.columns[1])
                day_prices[product].append(row.columns[15])
                day_pnls[product].append(row.columns[16])

            for product in day_timestamps:
                raw_ts = day_timestamps[product]
                offset_ts = [t + ts_offset for t in raw_ts]
                timestamps[product].extend(offset_ts)
                prices[product].extend(day_prices[product])
                pnls[product].extend(day_pnls[product])

            if day_timestamps:
                last_ts = max(max(v) for v in day_timestamps.values())
                ts_offset += last_ts + 100

        products = sorted(prices.keys())
        n = len(products)
        if n == 0:
            continue

        # Layout: one row per product, 2 columns (price | P&L)
        fig, axes = plt.subplots(
            n, 2,
            figsize=(16, max(3, n * 2.5)),
            sharex=False,
            squeeze=False,
        )
        fig.suptitle(f"Round {round_num}", fontsize=14, fontweight="bold", y=1.002)

        for row_idx, product in enumerate(products):
            ts = timestamps[product]
            px = prices[product]
            pl = pnls[product]

            ax_price = axes[row_idx][0]
            ax_pnl = axes[row_idx][1]

            ax_price.plot(ts, px, linewidth=0.8, color="#2196F3")
            ax_price.set_ylabel(product, fontsize=7, rotation=0, labelpad=80, va="center")
            ax_price.tick_params(labelsize=7)
            ax_price.grid(True, alpha=0.3)
            if row_idx == 0:
                ax_price.set_title("Mid Price", fontsize=9)

            final_color = "#4CAF50" if pl[-1] >= 0 else "#F44336"
            ax_pnl.plot(ts, pl, linewidth=0.8, color=final_color)
            ax_pnl.axhline(0, color="#888888", linewidth=0.6, linestyle="--")
            ax_pnl.tick_params(labelsize=7)
            ax_pnl.grid(True, alpha=0.3)
            if row_idx == 0:
                ax_pnl.set_title("P&L", fontsize=9)

        fig.tight_layout()

        out_path = output_dir / f"round{round_num}.png"
        fig.savefig(out_path, dpi=120, bbox_inches="tight")
        plt.close(fig)
        saved.append(out_path)
        print(f"Saved {out_path}")

    return saved
