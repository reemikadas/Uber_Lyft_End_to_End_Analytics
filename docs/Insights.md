# Uber vs Lyft Ride Pricing Insights

## Data Scope

The dashboard analyzes **637,976 valid fare quotes** collected across 18 observed dates from November 25 through December 18, 2018.

These records represent quoted fare estimates, not completed rides, bookings, revenue, or rider demand. Routes are directional, so `Back Bay → Fenway` and `Fenway → Back Bay` are treated separately.

The comparable service tiers are:

| Service tier | Lyft product | Uber product |
|---|---|---|
| Standard | Lyft | UberX |
| XL | Lyft XL | UberXL |
| Premium Black | Lux Black | Black |
| Premium Black XL | Lux Black XL | Black SUV |

## Executive Summary

- Lyft had slightly lower median pricing in the Standard and XL tiers.
- Uber had lower median pricing in both premium tiers.
- Total fare increased with distance, while price per mile decreased on longer routes.
- Daily median pricing was relatively stable during the limited observation period.
- Recorded surge appeared in 6.8% of all Lyft quotes and none of the Uber quotes.
- Fare-quote counts describe dataset coverage and should not be interpreted as ride demand or market share.

## Pricing by Service Tier

| Service tier | Lyft median fare | Uber median fare | Lyft difference | Lyft median $/mile | Uber median $/mile | Lyft difference |
|---|---:|---:|---:|---:|---:|---:|
| Standard | $9.00 | $9.50 | 5.3% lower | $4.57 | $4.67 | 2.1% lower |
| XL | $13.50 | $15.00 | 10.0% lower | $7.26 | $7.49 | 3.1% lower |
| Premium Black | $22.50 | $19.50 | 15.4% higher | $10.92 | $9.54 | 14.5% higher |
| Premium Black XL | $30.00 | $28.50 | 5.3% higher | $14.94 | $13.59 | 9.9% higher |

The provider advantage changes by service tier. Lyft was marginally less expensive for Standard and XL service, while Uber was generally less expensive for premium service.

The Standard-tier difference was small, suggesting that route and date may influence the better choice. The largest overall provider difference occurred in Premium Black, where Lyft's median price per mile was approximately 14.5% higher.

## Route-Level Findings

The route analysis covered 72 directional routes.

Based on route-level median price per mile:

| Service tier | Routes where Lyft was cheaper | Routes where Uber was cheaper | Equal median price per mile |
|---|---:|---:|---:|
| Standard | 48 of 72 | 24 of 72 | 0 |
| XL | 45 of 72 | 27 of 72 | 0 |
| Premium Black | 13 of 72 | 59 of 72 | 0 |
| Premium Black XL | 29 of 72 | 42 of 72 | 1 |

The route results reinforce the overall tier pattern. Lyft was more often cheaper in Standard and XL, while Uber was more often cheaper in Premium Black and Premium Black XL. One Premium Black XL route had the same median price per mile for both providers.

However, users should compare the selected route directly because individual routes can differ from the overall pattern.

## Distance and Pricing

Median fare and median route distance had a strong positive relationship across all provider-tier combinations. The route-level correlations ranged from approximately **0.94 to 0.98**, indicating that longer trips generally produced higher total fares.

Price per mile showed the opposite pattern. Its correlation with distance ranged from approximately **-0.73 to -0.81**.

This means:

- Longer trips generally cost more in total.
- Longer trips generally cost less per mile.
- Short trips can display unusually high price-per-mile values because base and fixed fare components are divided across fewer miles.

For short routes, total fare may therefore be more meaningful than price per mile alone.

## Pricing Over Time

Daily median price-per-mile results were relatively stable during the observed dates. Variation across the provider-tier daily series ranged from approximately **1.6% to 5.1%**.

The differences between service tiers were generally larger than the daily changes within a tier. This suggests that the selected service tier and route were stronger pricing differentiators than day-to-day movement during this short period.

Because only 18 dates were observed, these results should not be interpreted as evidence of long-term seasonality.

## Fare-Quote Coverage

The dataset contains:

| Provider | Fare quotes | Share of valid quotes |
|---|---:|---:|
| Uber | 330,568 | 51.8% |
| Lyft | 307,408 | 48.2% |

Uber has approximately 7% more records than Lyft within each comparable tier. However, the product-level counts are highly uniform, indicating that they primarily reflect how the source data was sampled.

Consequently, these counts should not be described as bookings, completed rides, customer preference, or provider market share.

## Recorded Surge

- Lyft recorded surge on **20,975 of 307,408 quotes**, or **6.8%** overall.
- Within each non-shared comparable Lyft tier, the recorded surge rate was approximately **8.2%**.
- No Uber quote had a recorded surge multiplier above `1`.

The dashboard correctly labels the Uber result as **No Recorded Surge**. It does not prove that Uber never used dynamic pricing. It only shows that the source `surge_multiplier` field did not record an Uber value above `1`.

Surge percentages can change when route, tier, and date filters are applied.

## Overall Conclusion

The analysis shows a clear service-tier tradeoff:

- Lyft offered a small historical price advantage in Standard and XL.
- Uber offered a more noticeable advantage in Premium Black and Premium Black XL.
- Distance increased total fare but reduced the calculated cost per mile.
- Route selection mattered, especially where provider differences were small.
- Recorded surge was present only for Lyft in this dataset.

These findings describe historical Boston fare estimates from November and December 2018. They should not be used as evidence of current pricing, actual bookings, realized revenue, or provider demand.
