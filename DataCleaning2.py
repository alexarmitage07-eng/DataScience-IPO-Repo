import csv
from datetime import date, datetime


def get_days_since_public(mdy_string: str) -> int:
    ipo_date = datetime.strptime(mdy_string, "%m/%d/%Y").date()
    return (date.today() - ipo_date).days


files = [
    "IPO_DATASET(2026_IPO_PRICING).csv",
    "IPO_DATASET(2025_IPO_PRICING).csv",
    "IPO_DATASET(2024_IPO_PRICING).csv",
]

integrated_file = []

for filename in files:
    with open(filename, "r", newline="") as f:
        reader = csv.reader(f)
        next(reader)  # skip header

        for row in reader:
            # Company (row[0]) is intentionally dropped: it sometimes carries
            # listing-method text in brackets (e.g. "(NASDAQ Direct Listing)"),
            # which is too sparse to analyse (37/232 in 2025) and fully
            # redundant with Ticker once stripped.
            ticker, industry, raw_date, shares, offer_price, first_day_close, current_price = row[1:8]

            # One row ("ZDAI (formerly PGHL)") carries the same
            # listing-note-in-brackets problem as Company. Strip it so
            # Ticker stays a bare symbol for every row.
            ticker = ticker.split(" (")[0]

            shares = float(shares)

            # Store money as integer cents, not float/double, to avoid
            # binary floating-point rounding errors on currency values.
            offer_price = round(float(offer_price.strip("$")) * 100)
            first_day_close = round(float(first_day_close.strip("$")) * 100)
            current_price = round(float(current_price.strip("$")) * 100)

            days_since_public = get_days_since_public(raw_date)

            # Source dates are US-style month/day/year; reformat to
            # Australian day/month/year for output.
            month, day, year = raw_date.split("/")
            display_date = f"{day}/{month}/{year}"

            # Return % is recalculated from offer/current price rather than
            # trusting the source's own return column, which contains
            # errors (e.g. a $4.00 -> $4.24 move mislabelled as 0.6% instead
            # of the correct 6%).
            # A handful of rows have a $0 offer price (bad source data) —
            # return on a $0 base is undefined, not a real 0% or error.
            if offer_price == 0:
                return_percent = None
            else:
                return_percent = ((current_price - offer_price) / offer_price) * 100

            integrated_file.append({
                "Ticker": ticker,
                "Industry": industry,
                "Date": display_date,
                "Shares": shares,
                "OfferPrice": offer_price,
                "FirstDayClose": first_day_close,
                "CurrentPrice": current_price,
                "Return": return_percent,
                "DaysSincePublic": days_since_public,
            })

fieldnames = [
    "Ticker", "Industry", "Date", "Shares", "OfferPrice",
    "FirstDayClose", "CurrentPrice", "Return", "DaysSincePublic",
]

with open("integrated_ipo_data.csv", "w", newline="") as out_file:
    writer = csv.DictWriter(out_file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(integrated_file)

print(f"Wrote {len(integrated_file)} rows to integrated_ipo_data.csv")