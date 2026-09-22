library(readr)
library(dplyr)
library(tidyr)
library(ggplot2)
library(forcats)
library(scales)

ipo <- read_csv("integrated_ipo_data.csv", show_col_types = FALSE)

# --- derive fields not stored in the cleaned CSV ---------------------------
# Prices are stored in cents (OfferPrice, FirstDayClose, CurrentPrice); convert to
# dollars for readability in charts/tables. OneDayReturn (offer -> first close)
# isn't in the CSV (which only stores current return), so compute it here.
# Valuation = Shares (millions) * OfferPrice (dollars) = raise size in $M.
ipo <- ipo %>%
  mutate(
    OfferPriceUSD = OfferPrice / 100,
    OneDayReturn = if_else(OfferPrice == 0, NA_real_, (FirstDayClose - OfferPrice) / OfferPrice * 100),
    Valuation = Shares * OfferPriceUSD
  )

# Rows with CurrentPrice == 0 make "current return" meaningless (flat -100%,
# likely reflects not-yet-quoted/no data rather than a real crash) - excluded
# from current-return analysis and reported as a limitation, not silently averaged in.
ipo_current <- ipo %>% filter(CurrentPrice > 0, !is.na(Return))

# ============================================================================
# Chart 1: Column graph - average 1-day and current return by industry
# ============================================================================
by_industry <- bind_rows(
  ipo %>% filter(!is.na(OneDayReturn)) %>%
    group_by(Industry) %>%
    summarise(Metric = "1-Day Return", Mean = mean(OneDayReturn), Median = median(OneDayReturn), n = n()),
  ipo_current %>%
    group_by(Industry) %>%
    summarise(Metric = "Current Return", Mean = mean(Return), Median = median(Return), n = n())
)

p1 <- ggplot(by_industry, aes(x = fct_reorder(Industry, Mean, .fun = mean), y = Mean, fill = Metric)) +
  geom_col(position = position_dodge(width = 0.8), width = 0.7) +
  geom_hline(yintercept = 0, linewidth = 0.4) +
  geom_text(aes(label = paste0("n=", n)), position = position_dodge(width = 0.8),
            vjust = -0.4, size = 2.6) +
  coord_flip() +
  labs(title = "Average IPO Return by Industry",
       subtitle = "1-day return (offer -> first close) vs current return (offer -> latest price)",
       x = NULL, y = "Average Return (%)", fill = NULL,
       caption = "Rows with $0 current price excluded from current-return average (see limitations).") +
  scale_fill_manual(values = c("1-Day Return" = "#4C72B0", "Current Return" = "#DD8452")) +
  theme_minimal(base_size = 11)

ggsave("chart1_return_by_industry.png", p1, width = 9, height = 6, dpi = 150)

# ============================================================================
# Chart 2: Column graph - average return by valuation quartile
# ============================================================================
val_bins <- ipo %>%
  filter(!is.na(Valuation)) %>%
  mutate(ValuationBin = ntile(Valuation, 4)) %>%
  mutate(ValuationBin = factor(ValuationBin, labels = c("Q1 (smallest)", "Q2", "Q3", "Q4 (largest)")))

by_valuation <- bind_rows(
  val_bins %>% filter(!is.na(OneDayReturn)) %>%
    group_by(ValuationBin) %>%
    summarise(Metric = "1-Day Return", Mean = mean(OneDayReturn), n = n()),
  val_bins %>% filter(CurrentPrice > 0, !is.na(Return)) %>%
    group_by(ValuationBin) %>%
    summarise(Metric = "Current Return", Mean = mean(Return), n = n())
)

p2 <- ggplot(by_valuation, aes(x = ValuationBin, y = Mean, fill = Metric)) +
  geom_col(position = position_dodge(width = 0.8), width = 0.7) +
  geom_hline(yintercept = 0, linewidth = 0.4) +
  geom_text(aes(label = paste0("n=", n)), position = position_dodge(width = 0.8),
            vjust = -0.4, size = 2.6) +
  labs(title = "Average IPO Return by Company Valuation",
       subtitle = "Valuation = Shares offered (M) x Offer Price, split into quartiles",
       x = "Valuation Quartile", y = "Average Return (%)", fill = NULL) +
  scale_fill_manual(values = c("1-Day Return" = "#4C72B0", "Current Return" = "#DD8452")) +
  theme_minimal(base_size = 11)

ggsave("chart2_return_by_valuation.png", p2, width = 8, height = 5.5, dpi = 150)

# ============================================================================
# Chart 3: Heatmap - average current return by month/year (recency trend)
# ============================================================================
ipo_time <- ipo_current %>%
  mutate(
    ParsedDate = as.Date(Date, format = "%d/%m/%Y"),
    Year = format(ParsedDate, "%Y"),
    Month = factor(format(ParsedDate, "%b"), levels = month.abb)
  )

by_month <- ipo_time %>%
  group_by(Year, Month) %>%
  summarise(Mean = mean(Return), n = n(), .groups = "drop")

p3 <- ggplot(by_month, aes(x = Month, y = Year, fill = Mean)) +
  geom_tile(color = "white", linewidth = 0.4) +
  geom_text(aes(label = paste0(round(Mean, 0), "%")), size = 2.8) +
  scale_fill_gradient2(low = "#B2182B", mid = "white", high = "#2166AC", midpoint = 0,
                        name = "Avg Current\nReturn (%)") +
  labs(title = "Average Current Return by IPO Month",
       subtitle = "Does the average return trend up or down as IPO cohorts age?",
       x = NULL, y = NULL) +
  theme_minimal(base_size = 11) +
  theme(panel.grid = element_blank())

ggsave("chart3_return_trend_heatmap.png", p3, width = 10, height = 4, dpi = 150)

cat("Saved chart1_return_by_industry.png, chart2_return_by_valuation.png, chart3_return_trend_heatmap.png\n")
