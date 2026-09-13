# Data Dictionary

## Dataset Overview

| Property | Value |
| --- | --- |
| Gold table | `rideshare_elt.gold.rides_weather_enriched` |
| Grain | One row per valid Uber or Lyft fare quote |
| Row count | 637,976 |
| Column count | 36 |
| Primary identifier | `id` |
| Providers | Uber and Lyft |
| Data period | November 25 through December 18, 2018 |
| Local timezone | America/New_York |
| Tableau export | `tableau/data/rideshare_gold.csv` |
| Predictive-model target | `price` |

A record represents a quoted fare, not a booking, completed ride, passenger,
or realized revenue transaction.

Weather observations are matched independently to the source and destination
locations using the nearest available observation within 60 minutes of the
fare-query timestamp.

## Service and Location Fields

| Column | Spark type | Description | Modeling role |
| --- | --- | --- | --- |
| `id` | String | Unique identifier for a fare quote. | Excluded identifier |
| `product_id` | String | Provider-specific identifier for the quoted ride product. | Excluded identifier |
| `cab_type` | String | Ride provider: Uber or Lyft. | Excluded because `name` identifies the provider-specific product |
| `name` | String | Provider-specific ride product, such as UberX, Black, Lyft, or Lux Black XL. | Categorical feature |
| `source` | String | Starting location associated with the fare quote. | Categorical feature |
| `destination` | String | Destination associated with the fare quote. | Categorical feature |
| `route` | String | Directional route formatted as `source → destination`. | Excluded because it is derived from `source` and `destination` |

## Fare and Distance Fields

| Column | Spark type | Unit/domain | Description | Modeling role |
| --- | --- | --- | --- | --- |
| `distance` | Double | Miles | Estimated distance associated with the fare quote. | Numeric feature |
| `price` | Double | USD | Quoted ride price. This is not realized revenue. | Prediction target |
| `surge_multiplier` | Double | Multiplier | Provider-recorded surge multiplier. A value of `1.0` indicates no recorded surge. | Numeric feature |
| `price_per_mile` | Double | USD per mile | Quoted price divided by distance and rounded to two decimal places. | Excluded target leakage |
| `surge_applied` | Boolean | `true` or `false` | Indicates whether `surge_multiplier > 1.0`. | Excluded because it duplicates information in `surge_multiplier` |

`price_per_mile` is excluded from price prediction because its calculation
directly uses the target:

```text
price_per_mile = price / distance
```

## Query Date and Time Fields

| Column | Spark type | Description | Modeling role |
| --- | --- | --- | --- |
| `query_datetime_utc` | Timestamp | Fare-query timestamp in Coordinated Universal Time. | Excluded raw timestamp |
| `query_datetime_local` | Timestamp | Fare-query timestamp converted to America/New_York time. | Excluded raw timestamp |
| `query_date_local` | Date | Local calendar date of the fare query. | Chronological splitting only |
| `query_hour_local` | Integer | Local hour of the query, from `0` through `23`. | Numeric feature |
| `query_day_name_local` | String | Local weekday name, such as Monday or Friday. | Categorical feature |
| `is_weekend` | Boolean | Indicates whether the local query date is Saturday or Sunday. | Categorical feature |

`query_date_local` determines the chronological train, validation, and test
periods. It is not supplied to the model as a predictor.

## Source Weather Fields

| Column | Spark type | Unit/domain | Description | Modeling role |
| --- | --- | --- | --- | --- |
| `source_temperature` | Double | Degrees Fahrenheit | Temperature from the weather observation matched to the source location. | Excluded due to redundancy with the engineered average temperature |
| `source_clouds` | Double | Proportion from 0 to 1 | Cloud-cover proportion at the source location. | Numeric feature |
| `source_pressure` | Double | Source-reported pressure | Atmospheric pressure at the source location. | Numeric feature |
| `source_rain_amount` | Double | Source-reported precipitation | Rain measurement at the source location. Missing rain values are represented as `0.0` for analysis. | Numeric feature |
| `source_humidity` | Double | Proportion from 0 to 1 | Relative humidity at the source location. | Numeric feature |
| `source_wind` | Double | Source-reported wind speed | Wind measurement at the source location. | Numeric feature |
| `source_is_raining` | Boolean | `true` or `false` | Indicates whether the source rain amount is greater than zero. | Excluded in favor of `rain_at_either_location` |

## Destination Weather Fields

| Column | Spark type | Unit/domain | Description | Modeling role |
| --- | --- | --- | --- | --- |
| `destination_temperature` | Double | Degrees Fahrenheit | Temperature from the weather observation matched to the destination. | Excluded due to redundancy |
| `destination_clouds` | Double | Proportion from 0 to 1 | Cloud-cover proportion at the destination. | Excluded due to high correlation with `source_clouds` |
| `destination_pressure` | Double | Source-reported pressure | Atmospheric pressure at the destination. | Excluded due to high correlation with `source_pressure` |
| `destination_rain_amount` | Double | Source-reported precipitation | Rain measurement at the destination. Missing rain values are represented as `0.0` for analysis. | Excluded due to high correlation with `source_rain_amount` |
| `destination_humidity` | Double | Proportion from 0 to 1 | Relative humidity at the destination. | Excluded due to high correlation with `source_humidity` |
| `destination_wind` | Double | Source-reported wind speed | Wind measurement at the destination. | Excluded due to high correlation with `source_wind` |
| `destination_is_raining` | Boolean | `true` or `false` | Indicates whether the destination rain amount is greater than zero. | Excluded in favor of `rain_at_either_location` |

The source and destination locations are geographically close. Their weather
variables are therefore highly correlated. The model retains a representative
source-weather measurement instead of including both copies.

## Engineered Weather Fields

| Column | Spark type | Unit/domain | Description | Modeling role |
| --- | --- | --- | --- | --- |
| `average_endpoint_temperature` | Double | Degrees Fahrenheit | Mean of the matched source and destination temperatures, rounded to two decimal places. | Numeric feature |
| `endpoint_temperature_difference` | Double | Degrees Fahrenheit | Absolute difference between the source and destination temperatures, rounded to two decimal places. | Numeric feature |
| `rain_at_either_location` | Boolean | `true` or `false` | Indicates whether rain was recorded at the source, destination, or both locations. | Categorical feature |

The engineered temperature fields are calculated as follows:

```text
average_endpoint_temperature =
    (source_temperature + destination_temperature) / 2

endpoint_temperature_difference =
    ABS(source_temperature - destination_temperature)

rain_at_either_location =
    source_is_raining OR destination_is_raining
```

## Pipeline Metadata

| Column | Spark type | Description | Modeling role |
| --- | --- | --- | --- |
| `_gold_created_at` | Timestamp | Timestamp showing when the Gold record was generated. | Excluded pipeline metadata |

`_gold_created_at` remains in the governed Gold Delta table for lineage and
refresh tracking. It is removed from the Tableau CSV export and predictive
modeling dataset.

## Final Predictive-Model Fields

### Target

```text
price
```

### Numeric Features

```text
distance
surge_multiplier
query_hour_local
source_clouds
source_pressure
source_rain_amount
source_humidity
source_wind
average_endpoint_temperature
endpoint_temperature_difference
```

### Categorical Features

```text
name
source
destination
query_day_name_local
is_weekend
rain_at_either_location
```

### Split Field

```text
query_date_local
```

### Excluded Fields

```text
id
product_id
cab_type
route
price_per_mile
surge_applied
query_datetime_utc
query_datetime_local
source_temperature
destination_temperature
destination_clouds
destination_pressure
destination_rain_amount
destination_humidity
destination_wind
source_is_raining
destination_is_raining
_gold_created_at
```

## Important Interpretation Notes

- `price` is a quoted fare, not realized revenue.
- Fare-quote counts must not be described as ride bookings.
- `price_per_mile` can be used for descriptive analysis but not as an input
  when predicting `price`.
- `surge_multiplier` reflects the provider-recorded multiplier in the source
  data. Uber records contain no multiplier greater than `1.0` in this dataset.
- Weather correlation with price is weak on its own, but retained weather
  features may contribute through nonlinear effects or interactions.
- The dataset covers a short historical period. Predictive results should not
  be interpreted as evidence of long-term or seasonal performance.
