import csv

import yfinance as yf

SRC = "integrated_ipo_data.csv"
TARGET_DATE = "2026-09-10"

with open(SRC, newline="") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

tickers = [r["Ticker"] for r in rows]

print(f"Fetching {TARGET_DATE} close for {len(tickers)} tickers from Yahoo Finance...")
data = yf.download(
    tickers,
    start=TARGET_DATE,
    end="2026-09-11",
    group_by="ticker",
    threads=True,
    progress=False,
)

close_by_ticker = {}
for ticker in tickers:
    try:
        series = data[ticker]["Close"]
    except (KeyError, TypeError):
        continue
    series = series.dropna()
    if not series.empty:
        close_by_ticker[ticker] = float(series.iloc[0])

updated, unchanged_no_data = 0, []
for r in rows:
    ticker = r["Ticker"]
    close = close_by_ticker.get(ticker)
    if close is None:
        unchanged_no_data.append(ticker)
        continue

    new_current_cents = round(close * 100)
    offer_cents = int(r["OfferPrice"])

    r["CurrentPrice"] = str(new_current_cents)
    r["Return"] = "" if offer_cents == 0 else str((new_current_cents - offer_cents) / offer_cents * 100)
    updated += 1

with open(SRC, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Updated CurrentPrice/Return for {updated} tickers using Yahoo Finance {TARGET_DATE} close.")
print(f"No Yahoo data found for {len(unchanged_no_data)} tickers (left unchanged):")
print(", ".join(unchanged_no_data))
