from datetime import date

import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

START = "2023-12-01"  # one month early, to compute Jan 2024's month-over-month return
END = date.today().isoformat()

data = yf.download("^GSPC", start=START, end=END, interval="1mo", progress=False)
closes = data["Close"]["^GSPC"]

month_abbrs = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Month-over-month % return: (this month's close - prior month's close) / prior close.
returns = closes.pct_change().dropna() * 100
returns = returns[(returns.index >= "2024-01-01")]

years = sorted({d.year for d in returns.index})
matrix = np.full((len(years), 12), np.nan)
for d, val in returns.items():
    yi = years.index(d.year)
    matrix[yi, d.month - 1] = val

norm = TwoSlopeNorm(vcenter=0, vmin=np.nanmin(matrix), vmax=np.nanmax(matrix))

fig, ax = plt.subplots(figsize=(10, 1.2 * len(years) + 1.5))
im = ax.imshow(matrix, cmap="RdBu", norm=norm, aspect="auto")
ax.set_xticks(range(12))
ax.set_xticklabels(month_abbrs)
ax.set_yticks(range(len(years)))
ax.set_yticklabels(years)
ax.set_title("S&P 500 Monthly Return (Jan 2024 - Sep 2026)")

for yi in range(len(years)):
    for mi in range(12):
        val = matrix[yi, mi]
        if not np.isnan(val):
            ax.text(mi, yi, f"{val:.1f}%", ha="center", va="center", fontsize=8)

fig.colorbar(im, ax=ax, label="Monthly Return (%)")
fig.text(0.01, 0.01, "Note: latest month is partial (data pulled before month-end).",
          fontsize=7, style="italic")
fig.tight_layout()
fig.savefig("mpl_chart4_spx_monthly_heatmap.png", dpi=150)
print("Saved mpl_chart4_spx_monthly_heatmap.png")
