import csv
import statistics
from collections import defaultdict
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

# --- load cleaned data -------------------------------------------------------
rows = []
with open("integrated_ipo_data.csv", newline="") as f:
    for r in csv.DictReader(f):
        offer_price = int(r["OfferPrice"])
        first_day_close = int(r["FirstDayClose"])
        current_price = int(r["CurrentPrice"])
        shares = float(r["Shares"])
        return_val = float(r["Return"]) if r["Return"] != "" else None

        # OneDayReturn and Valuation aren't stored in the cleaned CSV (which
        # only carries current return), so derive them here from the raw
        # price/share fields, same approach as the R version.
        one_day_return = None if offer_price == 0 else (first_day_close - offer_price) / offer_price * 100
        valuation = shares * offer_price / 100  # $ millions (Shares is millions, OfferPrice was cents)

        rows.append({
            "Industry": r["Industry"],
            "Date": r["Date"],  # DD/M/YYYY (Australian)
            "OfferPrice": offer_price,
            "CurrentPrice": current_price,
            "Return": return_val,
            "OneDayReturn": one_day_return,
            "Valuation": valuation,
        })

# Rows with CurrentPrice == 0 make "current return" meaningless (flat -100%,
# likely missing/not-yet-quoted data rather than a real crash) - excluded
# from every current-return aggregate below, same as the R version.


def grouped_means(rows, key_fn, one_day_filter=True):
    one_day = defaultdict(list)
    current = defaultdict(list)
    for row in rows:
        key = key_fn(row)
        if row["OneDayReturn"] is not None:
            one_day[key].append(row["OneDayReturn"])
        if row["CurrentPrice"] > 0 and row["Return"] is not None:
            current[key].append(row["Return"])
    return one_day, current


def mean_or_zero(values):
    return statistics.mean(values) if values else 0.0


# ============================================================================
# Chart 1: Column (bar) graph - average 1-day and current return by industry
# ============================================================================
one_day_by_industry, current_by_industry = grouped_means(rows, lambda r: r["Industry"])

industries = sorted(
    set(one_day_by_industry) | set(current_by_industry),
    key=lambda i: mean_or_zero(current_by_industry[i]),
)

means_one_day = [mean_or_zero(one_day_by_industry[i]) for i in industries]
means_current = [mean_or_zero(current_by_industry[i]) for i in industries]
n_one_day = [len(one_day_by_industry[i]) for i in industries]
n_current = [len(current_by_industry[i]) for i in industries]

y = np.arange(len(industries))
height = 0.35

fig, ax = plt.subplots(figsize=(9, 6))
bars1 = ax.barh(y - height / 2, means_one_day, height, label="1-Day Return", color="#3B7DD8")
bars2 = ax.barh(y + height / 2, means_current, height, label="Current Return", color="#E07B39")
ax.axvline(0, color="black", linewidth=0.8)
ax.set_yticks(y)
ax.set_yticklabels(industries)
ax.set_xlabel("Average Return (%)")
ax.set_title("Average IPO Return by Industry")
ax.legend(loc="lower right")

for bar, n in zip(bars1, n_one_day):
    ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f" n={n}",
            va="center", fontsize=7)
for bar, n in zip(bars2, n_current):
    ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f" n={n}",
            va="center", fontsize=7)

fig.tight_layout()
fig.savefig("mpl_chart1_return_by_industry.png", dpi=150)
plt.close(fig)

# ============================================================================
# Chart 2: Column graph - average return by valuation quartile
# ============================================================================
valuations = [row["Valuation"] for row in rows]
q1, q2, q3 = np.percentile(valuations, [25, 50, 75])
bin_labels = ["Q1 (smallest)", "Q2", "Q3", "Q4 (largest)"]


def valuation_bin(v):
    if v <= q1:
        return bin_labels[0]
    elif v <= q2:
        return bin_labels[1]
    elif v <= q3:
        return bin_labels[2]
    return bin_labels[3]


one_day_by_bin, current_by_bin = grouped_means(rows, lambda r: valuation_bin(r["Valuation"]))

means_one_day_v = [mean_or_zero(one_day_by_bin[b]) for b in bin_labels]
means_current_v = [mean_or_zero(current_by_bin[b]) for b in bin_labels]
n_one_day_v = [len(one_day_by_bin[b]) for b in bin_labels]
n_current_v = [len(current_by_bin[b]) for b in bin_labels]

x = np.arange(len(bin_labels))
width = 0.35

fig, ax = plt.subplots(figsize=(8, 5.5))
bars1 = ax.bar(x - width / 2, means_one_day_v, width, label="1-Day Return", color="#3B7DD8")
bars2 = ax.bar(x + width / 2, means_current_v, width, label="Current Return", color="#E07B39")
ax.axhline(0, color="black", linewidth=0.8)
ax.set_xticks(x)
ax.set_xticklabels(bin_labels)
ax.set_ylabel("Average Return (%)")
ax.set_title("Average IPO Return by Company Valuation")
ax.set_xlabel("Valuation quartile (Shares offered (M) x Offer Price)")
ax.legend()

for bar, n in zip(bars1, n_one_day_v):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"n={n}",
            ha="center", va="bottom" if bar.get_height() >= 0 else "top", fontsize=8)
for bar, n in zip(bars2, n_current_v):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"n={n}",
            ha="center", va="bottom" if bar.get_height() >= 0 else "top", fontsize=8)

fig.tight_layout()
fig.savefig("mpl_chart2_return_by_valuation.png", dpi=150)
plt.close(fig)

# ============================================================================
# Chart 3: Heatmap - average current return by month/year (recency trend)
# ============================================================================
month_abbrs = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

cell_returns = defaultdict(list)
years_seen = set()
for row in rows:
    if row["CurrentPrice"] <= 0 or row["Return"] is None:
        continue
    parsed = datetime.strptime(row["Date"], "%d/%m/%Y")
    years_seen.add(parsed.year)
    cell_returns[(parsed.year, parsed.month)].append(row["Return"])

years = sorted(years_seen)
matrix = np.full((len(years), 12), np.nan)
for yi, yr in enumerate(years):
    for mi in range(12):
        vals = cell_returns.get((yr, mi + 1))
        if vals:
            matrix[yi, mi] = statistics.mean(vals)

norm = TwoSlopeNorm(vcenter=0, vmin=np.nanmin(matrix), vmax=np.nanmax(matrix))

fig, ax = plt.subplots(figsize=(10, 1.2 * len(years) + 1.5))
im = ax.imshow(matrix, cmap="RdBu", norm=norm, aspect="auto")
ax.set_xticks(range(12))
ax.set_xticklabels(month_abbrs)
ax.set_yticks(range(len(years)))
ax.set_yticklabels(years)
ax.set_title("Average Current Return by IPO Month")

for yi in range(len(years)):
    for mi in range(12):
        val = matrix[yi, mi]
        if not np.isnan(val):
            ax.text(mi, yi, f"{val:.0f}%", ha="center", va="center", fontsize=8)

fig.colorbar(im, ax=ax, label="Avg Current Return (%)")
fig.tight_layout()
fig.savefig("mpl_chart3_return_trend_heatmap.png", dpi=150)
plt.close(fig)

print("Saved mpl_chart1_return_by_industry.png, mpl_chart2_return_by_valuation.png, "
      "mpl_chart3_return_trend_heatmap.png")
