# Databricks notebook source
# MAGIC %md
# MAGIC # Ride Fare Prediction
# MAGIC
# MAGIC **Project:** Uber/Lyft Databricks ELT Pipeline  
# MAGIC **Source:** `rideshare_elt.gold.rides_weather_enriched`  
# MAGIC **Target:** `price`  
# MAGIC **Task:** Supervised regression
# MAGIC
# MAGIC ## Objective
# MAGIC
# MAGIC Build and evaluate regression models that predict the quoted ride price using service, source, destination, distance, time, surge, and weather features.
# MAGIC
# MAGIC ## Modeling principles
# MAGIC
# MAGIC - Maintain one row per valid fare quote.
# MAGIC - Split the data before fitting preprocessing steps.
# MAGIC - Prevent target leakage.
# MAGIC - Exclude `price_per_mile` because it is calculated using the target price.
# MAGIC - Compare every model with a simple baseline.
# MAGIC - Evaluate performance using MAE, RMSE, and R².

# COMMAND ----------

from pyspark.sql import functions as F

gold_table = "rideshare_elt.gold.rides_weather_enriched"

if not spark.catalog.tableExists(gold_table):
    raise ValueError(f"Required Gold table was not found: {gold_table}")

model_source_df = spark.table(gold_table)

print(f"Source table: {gold_table}")
print(f"Rows: {model_source_df.count():,}")
print(f"Columns: {len(model_source_df.columns)}")

display(model_source_df.limit(10))

# COMMAND ----------

# validate the modeling grain and target
expected_rows = 637_976

source_validation = (
    model_source_df
    .agg(
        F.count("*").alias("total_rows"),
        F.countDistinct("id").alias("unique_quote_ids"),
        F.sum(F.col("price").isNull().cast("int")).alias("null_target_rows"),
        F.sum((F.col("price") < 0).cast("int")).alias("negative_target_rows"),
        F.min("price").alias("minimum_price"),
        F.max("price").alias("maximum_price")
    )
    .first()
)

if source_validation["total_rows"] != expected_rows:
    raise ValueError("Unexpected Gold row count.")

if source_validation["unique_quote_ids"] != expected_rows:
    raise ValueError("Duplicate or missing fare-quote IDs detected.")

if source_validation["null_target_rows"] != 0:
    raise ValueError("The target price contains null values.")

if source_validation["negative_target_rows"] != 0:
    raise ValueError("The target price contains negative values.")

print("Modeling source validation passed.")
print(f"Rows: {source_validation["total_rows"]:,}")
print(f"Unique quote IDs: {source_validation["unique_quote_ids"]:,}")
print(f"Null Target rows: {source_validation["null_target_rows"]:,}")
print(f"Negative Target rows: {source_validation["negative_target_rows"]:,}")
print(f"Price range: ${source_validation["minimum_price"]:,.2f} - ${source_validation["maximum_price"]:,.2f}")

# COMMAND ----------

# Remove leakage and pipeline metadata
modeling_df = (
    model_source_df
    .drop(
        "price_per_mile", # Target Leakage: calculated using price
        "_gold_created_at" # Pipeline metadata
    )
)

print(f"Source Columns: {len(model_source_df.columns)}")
print(f"Modeling Columns: {len(modeling_df.columns)}")

# COMMAND ----------

# Classify the columns
target_column = "price"

numeric_features = [
    "distance",
    "surge_multiplier",
    "query_hour_local",
    "source_temperature",
    "source_clouds",
    "source_pressure",
    "source_rain_amount",
    "source_humidity",
    "source_wind",
    "destination_temperature",
    "destination_clouds",
    "destination_pressure",
    "destination_rain_amount",
    "destination_humidity",
    "destination_wind",
    "average_endpoint_temperature",
    "endpoint_temperature_difference"
]

categorical_features = [
    "name",
    "source",
    "destination",
    "query_day_name_local",
    "is_weekend",
    "source_is_raining",
    "destination_is_raining",
    "rain_at_either_location"
]

excluded_columns = [
    "id",
    "product_id",
    "cab_type",
    "route",                    # Derived from source and destination
    "query_datetime_utc",
    "query_datetime_local",
    "query_date_local",         # Used only for chronological splitting
    "surge_applied"            # Redundant with surge_multiplier
]

print(f"Target Column: {target_column}")
print(f"Numeric Features: {len(numeric_features)}")
print(f"Categorical Features: {len(categorical_features)}")
print(f"Excluded Columns: {len(excluded_columns)}")

# COMMAND ----------

selected_columns = (
    [target_column]
    + numeric_features
    + categorical_features
    + excluded_columns
)

null_expressions = [
    F.sum(F.when(F.col(column_name).isNull(), 1).otherwise(0)).alias(column_name)
    for column_name in selected_columns
]

feature_null_summary_df = modeling_df.agg(*null_expressions)

print("Missing values in selected modeling columns:")
display(feature_null_summary_df)

# COMMAND ----------

# Check categorical cardinality
cardinality_expressions = [
    F.countDistinct(column_name).alias(column_name)
    for column_name in categorical_features
]

categorical_cardinality_df = modeling_df.agg(*cardinality_expressions)

print("Distinct values in categorical features:")
display(categorical_cardinality_df)

# COMMAND ----------

# Analyze the target distribution
price_summary_df = (
    modeling_df
    .agg(
        F.count("*").alias("fare_quotes"),
        F.round(F.avg("price"), 2).alias("average_price"),
        F.round(F.expr("percentile_approx(price, 0.25)"), 2).alias("price_p25"),
        F.round(F.expr("percentile_approx(price, 0.50)"), 2).alias("price_p50"),
        F.round(F.expr("percentile_approx(price, 0.75)"), 2).alias("price_p75"),
        F.round(F.stddev("price"), 2).alias("price_stddev"),
        F.min("price").alias("minimum_price"),
        F.max("price").alias("maximum_price")
    )
)

display(price_summary_df)

# COMMAND ----------

# Fare distribution by provider and product
price_by_product_df = (
    modeling_df
    .groupBy("cab_type", "name")
    .agg(
        F.count("*").alias("fare_quotes"),
        F.round(F.avg("price"), 2).alias("average_price"),
        F.round(F.expr("percentile_approx(price, 0.50)"), 2).alias("median_price"),
        F.min("price").alias("minimum_price"),
        F.max("price").alias("maximum_price")
    )
    .orderBy("cab_type", "median_price")
)

display(price_by_product_df)

# COMMAND ----------

# Calculate correlation with price
correlation_results = []

for feature_name in numeric_features:
    correlation_value = modeling_df.stat.corr(
        target_column,
        feature_name
    )

    correlation_results.append(
        (
            feature_name,
            float(correlation_value)
        )
    )

price_correlation_df = (
    spark.createDataFrame(
        correlation_results,
        [
            "feature",
            "correlation_with_price"
        ]
    )
    .withColumn(
        "absolute_correlation",
        F.abs("correlation_with_price")
    )
    .withColumn(
        "correlation_with_price",
        F.round("correlation_with_price", 4)
    )
    .withColumn(
        "absolute_correlation",
        F.round("absolute_correlation", 4)
    )
    .orderBy(F.desc("absolute_correlation"))
)

display(price_correlation_df)

# COMMAND ----------

from pyspark.ml.feature import VectorAssembler
from pyspark.ml.stat import Correlation
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

correlation_columns = (
    [target_column]
    + numeric_features
)

correlation_assembler = VectorAssembler(
    inputCols=correlation_columns,
    outputCol="correlation_features",
    handleInvalid="error"
)

correlation_vector_df = (
    correlation_assembler
    .transform(modeling_df.select(*correlation_columns))
    .select("correlation_features")
)

correlation_matrix = (
    Correlation
    .corr(
        correlation_vector_df,
        "correlation_features",
        "pearson"
    )
    .first()[0]
    .toArray()
)

correlation_matrix_pd = pd.DataFrame(
    correlation_matrix,
    index=correlation_columns,
    columns=correlation_columns
)

display(correlation_matrix_pd.round(3))

# COMMAND ----------

plt.figure(figsize=(16,12))

sns.heatmap(
    correlation_matrix_pd,
    cmap="coolwarm",
    center=0,
    vmin=-1,
    vmax=1,
    annot=True,
    fmt=".2f",
    linewidths=0.5
)

plt.title(
    "Correlation Matrix: Quoted Price and Numeric Features",
    fontsize=14
)

plt.xticks(rotation=45, ha="right")
plt.yticks(rotation=0)
plt.tight_layout()
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Final Feature Selection
# MAGIC
# MAGIC The correlation matrix identified substantial duplication between source and
# MAGIC destination weather measurements. The final feature set retains one
# MAGIC representative measurement or an engineered endpoint feature.

# COMMAND ----------

# Final feature set after correlation analysis

numeric_features = [
    "distance",
    "surge_multiplier",
    "query_hour_local",
    "source_clouds",
    "source_pressure",
    "source_rain_amount",
    "source_humidity",
    "source_wind",
    "average_endpoint_temperature",
    "endpoint_temperature_difference"
]

categorical_features = [
    "name",
    "source",
    "destination",
    "query_day_name_local",
    "is_weekend",
    "rain_at_either_location"
]

excluded_columns = [
    "id",
    "product_id",
    "cab_type",
    "route",
    "query_datetime_utc",
    "query_datetime_local",
    "query_date_local",
    "surge_applied",

    # Removed after correlation analysis
    "source_temperature",
    "destination_temperature",
    "destination_clouds",
    "destination_pressure",
    "destination_rain_amount",
    "destination_humidity",
    "destination_wind",
    "source_is_raining",
    "destination_is_raining"
]

selected_columns = (
    [target_column]
    + numeric_features
    + categorical_features
    + excluded_columns
)

print(f"Target columns: {len([target_column])}")
print(f"Final numeric features: {len(numeric_features)}")
print(f"Final categorical features: {len(categorical_features)}")
print(f"Excluded columns: {len(excluded_columns)}")
print(f"Total classified columns: {len(selected_columns)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Chronological Train, Validation, and Test Split
# MAGIC
# MAGIC Records are split chronologically to prevent future observations from
# MAGIC influencing models trained on earlier data. The test set remains untouched
# MAGIC until final model evaluation.

# COMMAND ----------

observed_dates = [
    row["query_date_local"]
    for row in (
        modeling_df
        .select("query_date_local")
        .distinct()
        .orderBy("query_date_local")
        .collect()
    )
]

number_of_dates = len(observed_dates)

train_date_count = int(number_of_dates * 2 / 3) # (18 * 2/3) = 12
remaining_date_count = number_of_dates - train_date_count # 18 - 12 = 6
validation_date_count = remaining_date_count // 2 # 6 // 2 = 3

train_end_date = observed_dates[train_date_count - 1]
validation_end_date = observed_dates[train_date_count + validation_date_count - 1]

train_df = modeling_df.filter(
    F.col("query_date_local") <= F.lit(train_end_date)
)

validation_df = modeling_df.filter(
    (F.col("query_date_local") > F.lit(train_end_date))
    &
    (F.col("query_date_local") <= F.lit(validation_end_date))
)

test_df = modeling_df.filter(
    F.col("query_date_local") > F.lit(validation_end_date)
)

print(f"Observed dates: {number_of_dates}")
print(f"Training through: {train_end_date}")
print(f"Validation through: {validation_end_date}")
print(f"Testing begins: {observed_dates[train_date_count + validation_date_count]}")

# COMMAND ----------

split_summary_df = (
    train_df.select(
        F.lit("Train").alias("split"),
        F.count("*").alias("rows"),
        F.min("query_date_local").alias("start_date"),
        F.max("query_date_local").alias("end_date")
    )
    .unionByName(
        validation_df.select(
            F.lit("Validation").alias("split"),
            F.count("*").alias("rows"),
            F.min("query_date_local").alias("start_date"),
            F.max("query_date_local").alias("end_date")
        )
    )
    .unionByName(
        test_df.select(
            F.lit("Test").alias("split"),
            F.count("*").alias("rows"),
            F.min("query_date_local").alias("start_date"),
            F.max("query_date_local").alias("end_date")
        )
    )
    .withColumn(
        "row_percentage",
        F.round(F.col("rows") / modeling_df.count() * 100, 2)
    )
)

display(split_summary_df)

# COMMAND ----------

split_row_count = (
    train_df.count()
    + validation_df.count()
    + test_df.count()
)

assert split_row_count == modeling_df.count(), (
    "Split row counts does not match the modeling dataset."
)

print(f"Chronological split validation passed: {split_row_count:,} rows")