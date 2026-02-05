# Databricks notebook source
# MAGIC %md
# MAGIC # Consumption Forecaster
# MAGIC ## Prophet-Based Contract Consumption Forecasting
# MAGIC
# MAGIC This notebook trains and runs Prophet models to predict contract consumption
# MAGIC and calculate probabilistic exhaustion dates.
# MAGIC
# MAGIC **Features:**
# MAGIC - Time series forecasting with Facebook Prophet
# MAGIC - Confidence intervals (p10, p50, p90)
# MAGIC - MLflow experiment tracking
# MAGIC - Automatic fallback for insufficient data
# MAGIC
# MAGIC **Version:** 1.0.0

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Setup & Configuration

# COMMAND ----------

# Debug logging setup - writes to a table for easy retrieval
import datetime as dt

DEBUG_LOG = []

def log_debug(message):
    """Log debug message with timestamp"""
    timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    DEBUG_LOG.append(log_entry)
    print(log_entry)

def save_debug_log():
    """Save debug log to a Delta table"""
    try:
        log_text = "\n".join(DEBUG_LOG)
        spark.sql(f"""
            CREATE TABLE IF NOT EXISTS main.account_monitoring_dev.forecast_debug_log (
                run_id STRING,
                timestamp TIMESTAMP,
                log_text STRING
            ) USING DELTA
        """)
        run_id = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        spark.sql(f"""
            INSERT INTO main.account_monitoring_dev.forecast_debug_log
            VALUES ('{run_id}', CURRENT_TIMESTAMP(), '{log_text.replace("'", "''")}')
        """)
        print(f"Debug log saved with run_id: {run_id}")
    except Exception as e:
        print(f"Failed to save debug log: {e}")

log_debug("=== FORECASTER NOTEBOOK STARTED ===")

# Widget parameters
try:
    log_debug("Setting up widgets...")
    dbutils.widgets.dropdown("mode", "both", ["training", "inference", "both"], "Execution Mode")
    dbutils.widgets.text("forecast_horizon_days", "365", "Forecast Horizon (days)")
    dbutils.widgets.text("confidence_interval", "0.80", "Confidence Interval")
    dbutils.widgets.text("min_training_days", "30", "Minimum Training Days")
    log_debug("Widgets created successfully")
except Exception as e:
    log_debug(f"Error creating widgets: {e}")

# Get widget values
try:
    MODE = dbutils.widgets.get("mode")
    FORECAST_HORIZON_DAYS = int(dbutils.widgets.get("forecast_horizon_days"))
    CONFIDENCE_INTERVAL = float(dbutils.widgets.get("confidence_interval"))
    MIN_TRAINING_DAYS = int(dbutils.widgets.get("min_training_days"))
    log_debug(f"Mode: {MODE}")
    log_debug(f"Forecast Horizon: {FORECAST_HORIZON_DAYS} days")
    log_debug(f"Confidence Interval: {CONFIDENCE_INTERVAL}")
    log_debug(f"Minimum Training Days: {MIN_TRAINING_DAYS}")
except Exception as e:
    log_debug(f"Error getting widget values: {e}")
    MODE = "inference"
    FORECAST_HORIZON_DAYS = 365
    CONFIDENCE_INTERVAL = 0.80
    MIN_TRAINING_DAYS = 30

# COMMAND ----------

# Try to import Prophet, fall back to linear-only mode if not available
log_debug("Checking Prophet availability...")
PROPHET_AVAILABLE = False
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
    log_debug("Prophet is available")
except ImportError:
    try:
        log_debug("Prophet not found, attempting install...")
        import subprocess
        subprocess.check_call(["pip", "install", "prophet", "-q"])
        from prophet import Prophet
        PROPHET_AVAILABLE = True
        log_debug("Prophet installed successfully")
    except Exception as e:
        log_debug(f"Warning: Prophet not available ({e}). Using linear projection only.")
        PROPHET_AVAILABLE = False

# COMMAND ----------

# Standard imports
log_debug("Importing standard libraries...")
try:
    from pyspark.sql import functions as F
    from pyspark.sql.types import *
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    import uuid
    log_debug("Standard imports successful")
except Exception as e:
    log_debug(f"Error in standard imports: {e}")
    save_debug_log()
    raise

# MLflow for experiment tracking
log_debug("Importing MLflow...")
try:
    import mlflow
    from mlflow.tracking import MlflowClient
    log_debug("MLflow import successful")
except Exception as e:
    log_debug(f"Error importing MLflow: {e}")
    save_debug_log()
    raise

# Visualization
log_debug("Importing plotly...")
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    log_debug("Plotly import successful")
except Exception as e:
    log_debug(f"Error importing plotly: {e}")
    save_debug_log()
    raise

# Configuration
CATALOG = "main"
SCHEMA = "account_monitoring_dev"
EXPERIMENT_NAME = f"/Shared/consumption_forecaster"

log_debug(f"Using catalog: {CATALOG}, schema: {SCHEMA}")
log_debug(f"MLflow experiment: {EXPERIMENT_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Data Loading

# COMMAND ----------

def load_contract_burndown_data():
    """Load historical daily costs from contract_burndown table."""
    query = f"""
    SELECT
      contract_id,
      cloud_provider,
      start_date,
      end_date,
      commitment,
      usage_date,
      daily_cost,
      cumulative_cost
    FROM {CATALOG}.{SCHEMA}.contract_burndown
    WHERE daily_cost IS NOT NULL
    ORDER BY contract_id, usage_date
    """
    return spark.sql(query).toPandas()

def load_active_contracts():
    """Load active contract information."""
    query = f"""
    SELECT
      contract_id,
      account_id,
      cloud_provider,
      start_date,
      end_date,
      total_value,
      currency,
      commitment_type,
      status
    FROM {CATALOG}.{SCHEMA}.contracts
    WHERE status = 'ACTIVE'
    """
    return spark.sql(query).toPandas()

# Load data
log_debug("Loading contract burndown data...")
try:
    burndown_df = load_contract_burndown_data()
    log_debug(f"Loaded {len(burndown_df)} burndown records")
except Exception as e:
    log_debug(f"Error loading burndown data: {e}")
    save_debug_log()
    raise

log_debug("Loading active contracts...")
try:
    contracts_df = load_active_contracts()
    log_debug(f"Found {len(contracts_df)} active contracts")
except Exception as e:
    log_debug(f"Error loading contracts: {e}")
    save_debug_log()
    raise

if not burndown_df.empty:
    log_debug(f"Date range: {burndown_df['usage_date'].min()} to {burndown_df['usage_date'].max()}")
    log_debug(f"Contracts: {burndown_df['contract_id'].unique().tolist()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Feature Engineering

# COMMAND ----------

def prepare_prophet_data(df, contract_id):
    """
    Prepare data in Prophet format (ds, y) for a specific contract.

    Args:
        df: DataFrame with burndown data
        contract_id: Contract to prepare data for

    Returns:
        DataFrame with ds (date) and y (daily_cost) columns
    """
    contract_data = df[df['contract_id'] == contract_id].copy()

    if contract_data.empty:
        return None

    # Prophet requires 'ds' (date) and 'y' (value) columns
    prophet_df = pd.DataFrame({
        'ds': pd.to_datetime(contract_data['usage_date']),
        'y': contract_data['daily_cost'].astype(float)
    })

    # Sort by date
    prophet_df = prophet_df.sort_values('ds').reset_index(drop=True)

    # Fill missing dates with 0 (no spend on those days)
    if len(prophet_df) > 1:
        date_range = pd.date_range(start=prophet_df['ds'].min(), end=prophet_df['ds'].max())
        prophet_df = prophet_df.set_index('ds').reindex(date_range).fillna(0).reset_index()
        prophet_df.columns = ['ds', 'y']

    return prophet_df

# Test data preparation
if not burndown_df.empty:
    sample_contract = burndown_df['contract_id'].iloc[0]
    sample_data = prepare_prophet_data(burndown_df, sample_contract)
    print(f"Sample data for contract {sample_contract}:")
    print(f"  Records: {len(sample_data)}")
    print(f"  Date range: {sample_data['ds'].min()} to {sample_data['ds'].max()}")
    display(sample_data.head(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Model Training

# COMMAND ----------

def train_prophet_model(df, contract_id, interval_width=0.80):
    """
    Train a Prophet model for a specific contract.

    Args:
        df: Full burndown DataFrame
        contract_id: Contract to train for
        interval_width: Confidence interval width (default 0.80 for p10/p90)

    Returns:
        Trained Prophet model and training metrics
    """
    if not PROPHET_AVAILABLE:
        return None, None, "Prophet not available"

    # Prepare data
    prophet_df = prepare_prophet_data(df, contract_id)

    if prophet_df is None or len(prophet_df) < MIN_TRAINING_DAYS:
        return None, None, f"Insufficient data: {len(prophet_df) if prophet_df is not None else 0} days (need {MIN_TRAINING_DAYS})"

    try:
        # Initialize Prophet with configuration
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            seasonality_mode='multiplicative',
            interval_width=interval_width,
            changepoint_prior_scale=0.05
        )

        # Add monthly seasonality
        model.add_seasonality(
            name='monthly',
            period=30.5,
            fourier_order=5
        )

        # Fit the model
        model.fit(prophet_df)

        # Calculate metrics using cross-validation (if enough data)
        metrics = {
            'training_points': len(prophet_df),
            'training_start': prophet_df['ds'].min(),
            'training_end': prophet_df['ds'].max(),
            'mape': None,
            'rmse': None,
            'mae': None
        }

        # Simple in-sample metrics
        fitted = model.predict(prophet_df)
        actuals = prophet_df['y'].values
        predictions = fitted['yhat'].values

        # Avoid division by zero
        non_zero_mask = actuals > 0
        if non_zero_mask.any():
            metrics['mape'] = np.mean(np.abs((actuals[non_zero_mask] - predictions[non_zero_mask]) / actuals[non_zero_mask])) * 100

        metrics['rmse'] = np.sqrt(np.mean((actuals - predictions) ** 2))
        metrics['mae'] = np.mean(np.abs(actuals - predictions))

        return model, metrics, None

    except Exception as e:
        return None, None, f"Training failed: {str(e)}"

# COMMAND ----------

def linear_fallback_forecast(df, contract_id, contract_info, forecast_days):
    """
    Fallback linear projection when Prophet cannot be used.

    Args:
        df: Burndown DataFrame
        contract_id: Contract ID
        contract_info: Contract details
        forecast_days: Number of days to forecast

    Returns:
        DataFrame with forecast results
    """
    contract_data = df[df['contract_id'] == contract_id].copy()

    if contract_data.empty:
        return None

    # Calculate average daily spend (convert to float to avoid Decimal issues)
    total_days = len(contract_data)
    total_spent = float(contract_data['cumulative_cost'].max())
    daily_avg = total_spent / total_days if total_days > 0 else 0.0

    # Generate forecast dates
    last_date = pd.to_datetime(contract_data['usage_date'].max())
    future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=forecast_days)

    # Linear projection
    forecast_df = pd.DataFrame({
        'ds': future_dates,
        'yhat': daily_avg,
        'yhat_lower': daily_avg * 0.8,  # Simple 20% band
        'yhat_upper': daily_avg * 1.2
    })

    return forecast_df

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Inference (Generate Forecasts)

# COMMAND ----------

def calculate_exhaustion_dates(forecast_df, contract_value, cumulative_spent):
    """
    Find when cumulative predicted cost exceeds contract value.
    Returns p10 (optimistic), p50 (median), p90 (conservative) dates.

    Args:
        forecast_df: Prophet forecast DataFrame
        contract_value: Total contract value
        cumulative_spent: Amount already spent

    Returns:
        Tuple of (p10_date, p50_date, p90_date, days_to_exhaustion)
    """
    remaining_budget = float(contract_value) - float(cumulative_spent)

    if remaining_budget <= 0:
        # Already exhausted
        return None, None, None, 0

    # Calculate cumulative forecasts
    forecast_df = forecast_df.copy()
    forecast_df['cumulative_yhat'] = forecast_df['yhat'].cumsum()
    forecast_df['cumulative_lower'] = forecast_df['yhat_lower'].cumsum()
    forecast_df['cumulative_upper'] = forecast_df['yhat_upper'].cumsum()

    # Find exhaustion dates
    p50_mask = forecast_df['cumulative_yhat'] >= remaining_budget
    p10_mask = forecast_df['cumulative_upper'] >= remaining_budget  # Upper bound = earlier exhaustion
    p90_mask = forecast_df['cumulative_lower'] >= remaining_budget  # Lower bound = later exhaustion

    p50_date = forecast_df.loc[p50_mask, 'ds'].min() if p50_mask.any() else None
    p10_date = forecast_df.loc[p10_mask, 'ds'].min() if p10_mask.any() else None
    p90_date = forecast_df.loc[p90_mask, 'ds'].min() if p90_mask.any() else None

    # Calculate days to exhaustion (median)
    if p50_date is not None:
        days_to_exhaustion = (p50_date - forecast_df['ds'].min()).days
    else:
        days_to_exhaustion = None

    return p10_date, p50_date, p90_date, days_to_exhaustion

# COMMAND ----------

def generate_forecast(model, contract_info, burndown_df):
    """
    Generate forecast for a contract using trained Prophet model.

    Args:
        model: Trained Prophet model
        contract_info: Contract details (row from contracts_df)
        burndown_df: Historical burndown data

    Returns:
        DataFrame with forecast results
    """
    contract_id = contract_info['contract_id']
    contract_end = pd.to_datetime(contract_info['end_date'])
    contract_value = float(contract_info['total_value'])

    # Get current cumulative spend
    contract_data = burndown_df[burndown_df['contract_id'] == contract_id]
    if contract_data.empty:
        return None

    last_date = pd.to_datetime(contract_data['usage_date'].max())
    cumulative_spent = float(contract_data['cumulative_cost'].max())

    # Calculate days to forecast (until contract end + buffer)
    days_to_end = max((contract_end - last_date).days, 0)
    forecast_days = min(days_to_end + 90, FORECAST_HORIZON_DAYS)  # Add 90 day buffer

    if forecast_days <= 0:
        return None

    # Generate future dataframe
    future = model.make_future_dataframe(periods=forecast_days)

    # Predict
    forecast = model.predict(future)

    # Filter to future only
    future_forecast = forecast[forecast['ds'] > last_date].copy()

    # Calculate exhaustion dates
    p10_date, p50_date, p90_date, days_to_exhaustion = calculate_exhaustion_dates(
        future_forecast, contract_value, cumulative_spent
    )

    # Prepare result DataFrame
    result = pd.DataFrame({
        'contract_id': contract_id,
        'forecast_date': future_forecast['ds'],
        'predicted_daily_cost': future_forecast['yhat'].clip(lower=0),  # No negative costs
        'lower_bound': future_forecast['yhat_lower'].clip(lower=0),
        'upper_bound': future_forecast['yhat_upper'].clip(lower=0),
        'exhaustion_date_p10': p10_date,
        'exhaustion_date_p50': p50_date,
        'exhaustion_date_p90': p90_date,
        'days_to_exhaustion': days_to_exhaustion
    })

    # Add cumulative predictions
    result['predicted_cumulative'] = cumulative_spent + result['predicted_daily_cost'].cumsum()

    return result

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Main Execution

# COMMAND ----------

def run_training(burndown_df, contracts_df):
    """
    Train Prophet models for all active contracts.

    Returns:
        Dictionary mapping contract_id to trained model
    """
    # Set up MLflow experiment
    mlflow.set_experiment(EXPERIMENT_NAME)

    models = {}
    model_records = []

    for _, contract in contracts_df.iterrows():
        contract_id = contract['contract_id']
        print(f"\n{'='*50}")
        print(f"Training model for contract: {contract_id}")

        with mlflow.start_run(run_name=f"contract_{contract_id}"):
            # Log parameters
            mlflow.log_param("contract_id", contract_id)
            mlflow.log_param("confidence_interval", CONFIDENCE_INTERVAL)
            mlflow.log_param("min_training_days", MIN_TRAINING_DAYS)

            # Train model
            model, metrics, error = train_prophet_model(
                burndown_df, contract_id, CONFIDENCE_INTERVAL
            )

            if error:
                print(f"  Skipping: {error}")
                mlflow.log_param("status", "skipped")
                mlflow.log_param("error", error)
                continue

            # Log metrics
            if metrics['mape'] is not None:
                mlflow.log_metric("mape", metrics['mape'])
            if metrics['rmse'] is not None:
                mlflow.log_metric("rmse", metrics['rmse'])
            if metrics['mae'] is not None:
                mlflow.log_metric("mae", metrics['mae'])
            mlflow.log_metric("training_points", metrics['training_points'])

            # Store model
            models[contract_id] = model

            # Record for database (convert numpy types to Python native types)
            model_records.append({
                'model_id': str(uuid.uuid4()),
                'contract_id': contract_id,
                'trained_at': datetime.now(),
                'training_start_date': pd.Timestamp(metrics['training_start']).to_pydatetime().date() if metrics['training_start'] is not None else None,
                'training_end_date': pd.Timestamp(metrics['training_end']).to_pydatetime().date() if metrics['training_end'] is not None else None,
                'training_points': int(metrics['training_points']) if metrics['training_points'] is not None else None,
                'mape': float(metrics['mape']) if metrics['mape'] is not None else None,
                'rmse': float(metrics['rmse']) if metrics['rmse'] is not None else None,
                'mae': float(metrics['mae']) if metrics['mae'] is not None else None,
                'mlflow_experiment_id': mlflow.active_run().info.experiment_id,
                'mlflow_run_id': mlflow.active_run().info.run_id,
                'is_active': True
            })

            print(f"  Training points: {metrics['training_points']}")
            print(f"  MAPE: {metrics['mape']:.2f}%" if metrics['mape'] else "  MAPE: N/A")
            print(f"  RMSE: ${metrics['rmse']:.2f}" if metrics['rmse'] else "  RMSE: N/A")

    # Save model registry to database using SQL INSERT
    if model_records:
        # Deactivate old models
        contract_ids = ','.join([f"'{r['contract_id']}'" for r in model_records])
        spark.sql(f"""
            UPDATE {CATALOG}.{SCHEMA}.forecast_model_registry
            SET is_active = FALSE
            WHERE contract_id IN ({contract_ids})
        """)

        # Insert new records using SQL for better type handling
        for r in model_records:
            mape_val = f"{round(r['mape'], 4)}" if r['mape'] is not None else "NULL"
            rmse_val = f"{round(r['rmse'], 4)}" if r['rmse'] is not None else "NULL"
            mae_val = f"{round(r['mae'], 4)}" if r['mae'] is not None else "NULL"
            training_start = f"'{r['training_start_date']}'" if r['training_start_date'] is not None else "NULL"
            training_end = f"'{r['training_end_date']}'" if r['training_end_date'] is not None else "NULL"

            insert_sql = f"""
                INSERT INTO {CATALOG}.{SCHEMA}.forecast_model_registry
                (model_id, contract_id, trained_at, training_start_date, training_end_date,
                 training_points, mape, rmse, mae, mlflow_experiment_id, mlflow_run_id, is_active)
                VALUES (
                    '{r['model_id']}',
                    '{r['contract_id']}',
                    CURRENT_TIMESTAMP(),
                    {training_start},
                    {training_end},
                    {r['training_points'] if r['training_points'] is not None else 'NULL'},
                    {mape_val},
                    {rmse_val},
                    {mae_val},
                    '{r['mlflow_experiment_id']}',
                    '{r['mlflow_run_id']}',
                    TRUE
                )
            """
            spark.sql(insert_sql)

        print(f"\n{'='*50}")
        print(f"Saved {len(model_records)} model records to registry")

    return models

# COMMAND ----------

def run_inference(models, burndown_df, contracts_df):
    """
    Generate forecasts for all contracts with trained models.
    Falls back to linear projection if no model available.
    """
    all_forecasts = []

    for _, contract in contracts_df.iterrows():
        contract_id = contract['contract_id']
        print(f"\nGenerating forecast for contract: {contract_id}")

        if contract_id in models and models[contract_id] is not None:
            # Use Prophet model
            forecast = generate_forecast(models[contract_id], contract, burndown_df)
            model_version = "prophet"
        else:
            # Use linear fallback
            print(f"  Using linear fallback (no trained model)")
            contract_data = burndown_df[burndown_df['contract_id'] == contract_id]
            if contract_data.empty:
                print(f"  Skipping: No historical data")
                continue

            last_date = pd.to_datetime(contract_data['usage_date'].max())
            contract_end = pd.to_datetime(contract['end_date'])
            forecast_days = max((contract_end - last_date).days + 90, 30)

            forecast = linear_fallback_forecast(burndown_df, contract_id, contract, forecast_days)
            if forecast is None:
                continue

            # Calculate exhaustion for linear forecast
            cumulative_spent = float(contract_data['cumulative_cost'].max())
            contract_value = float(contract['total_value'])
            p10_date, p50_date, p90_date, days_to_exhaustion = calculate_exhaustion_dates(
                forecast.rename(columns={'yhat': 'yhat', 'yhat_lower': 'yhat_lower', 'yhat_upper': 'yhat_upper'}),
                contract_value, cumulative_spent
            )

            forecast = pd.DataFrame({
                'contract_id': contract_id,
                'forecast_date': forecast['ds'],
                'predicted_daily_cost': forecast['yhat'].clip(lower=0),
                'lower_bound': forecast['yhat_lower'].clip(lower=0),
                'upper_bound': forecast['yhat_upper'].clip(lower=0),
                'exhaustion_date_p10': p10_date,
                'exhaustion_date_p50': p50_date,
                'exhaustion_date_p90': p90_date,
                'days_to_exhaustion': days_to_exhaustion,
                'predicted_cumulative': cumulative_spent + forecast['yhat'].clip(lower=0).cumsum()
            })
            model_version = "linear_fallback"

        if forecast is not None and not forecast.empty:
            forecast['model_version'] = model_version
            forecast['created_at'] = datetime.now()
            all_forecasts.append(forecast)

            # Print summary
            p50 = forecast['exhaustion_date_p50'].iloc[0]
            print(f"  Forecast generated: {len(forecast)} days")
            print(f"  Predicted exhaustion (p50): {p50}" if pd.notna(p50) else "  Predicted exhaustion: Beyond forecast horizon")

    return all_forecasts

# COMMAND ----------

def save_forecasts(forecasts):
    """Save forecasts to the contract_forecast table."""
    if not forecasts:
        log_debug("No forecasts to save")
        return

    log_debug(f"Saving {len(forecasts)} forecast batches...")

    # Combine all forecasts
    combined_df = pd.concat(forecasts, ignore_index=True)
    log_debug(f"Combined {len(combined_df)} forecast records")

    # Clean up data types - convert dates
    combined_df['forecast_date'] = pd.to_datetime(combined_df['forecast_date']).dt.date

    # Handle nullable date columns
    for col in ['exhaustion_date_p10', 'exhaustion_date_p50', 'exhaustion_date_p90']:
        if col in combined_df.columns:
            combined_df[col] = pd.to_datetime(combined_df[col], errors='coerce')
            combined_df[col] = combined_df[col].apply(lambda x: x.date() if pd.notna(x) else None)

    # Convert numeric columns to Python floats (not numpy)
    for col in ['predicted_daily_cost', 'predicted_cumulative', 'lower_bound', 'upper_bound']:
        if col in combined_df.columns:
            combined_df[col] = combined_df[col].apply(lambda x: float(x) if pd.notna(x) else None)

    # Ensure days_to_exhaustion is int
    if 'days_to_exhaustion' in combined_df.columns:
        combined_df['days_to_exhaustion'] = combined_df['days_to_exhaustion'].apply(
            lambda x: int(x) if pd.notna(x) else None
        )

    # Create Spark DataFrame without explicit schema (let Spark infer types)
    # Then write using SQL for proper type handling
    log_debug("Writing forecasts via SQL INSERT...")

    # Clear existing data
    spark.sql(f"DELETE FROM {CATALOG}.{SCHEMA}.contract_forecast WHERE 1=1")

    # Insert in batches
    batch_size = 100
    total_inserted = 0
    for i in range(0, len(combined_df), batch_size):
        batch = combined_df.iloc[i:i+batch_size]
        values = []
        for _, row in batch.iterrows():
            # Format values for SQL
            contract_id = str(row['contract_id'])
            forecast_date = row['forecast_date']
            model_version = str(row.get('model_version', 'linear_fallback') or 'linear_fallback')
            pred_daily = round(row['predicted_daily_cost'], 2) if pd.notna(row.get('predicted_daily_cost')) else 'NULL'
            pred_cum = round(row['predicted_cumulative'], 2) if pd.notna(row.get('predicted_cumulative')) else 'NULL'
            lower = round(row['lower_bound'], 2) if pd.notna(row.get('lower_bound')) else 'NULL'
            upper = round(row['upper_bound'], 2) if pd.notna(row.get('upper_bound')) else 'NULL'
            ex_p10 = f"'{row['exhaustion_date_p10']}'" if pd.notna(row.get('exhaustion_date_p10')) else 'NULL'
            ex_p50 = f"'{row['exhaustion_date_p50']}'" if pd.notna(row.get('exhaustion_date_p50')) else 'NULL'
            ex_p90 = f"'{row['exhaustion_date_p90']}'" if pd.notna(row.get('exhaustion_date_p90')) else 'NULL'
            days = int(row['days_to_exhaustion']) if pd.notna(row.get('days_to_exhaustion')) else 'NULL'

            values.append(f"('{contract_id}', '{forecast_date}', '{model_version}', {pred_daily}, {pred_cum}, {lower}, {upper}, {ex_p10}, {ex_p50}, {ex_p90}, {days}, CURRENT_TIMESTAMP())")

        if values:
            insert_sql = f"""
                INSERT INTO {CATALOG}.{SCHEMA}.contract_forecast
                (contract_id, forecast_date, model_version, predicted_daily_cost, predicted_cumulative,
                 lower_bound, upper_bound, exhaustion_date_p10, exhaustion_date_p50, exhaustion_date_p90,
                 days_to_exhaustion, created_at)
                VALUES {', '.join(values)}
            """
            spark.sql(insert_sql)
            total_inserted += len(values)

    log_debug(f"Saved {total_inserted} forecast records to {CATALOG}.{SCHEMA}.contract_forecast")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Execute Based on Mode

# COMMAND ----------

# Check if we have data
log_debug("Checking if data is available...")
if burndown_df.empty or contracts_df.empty:
    log_debug("No data available for forecasting")
    save_debug_log()
    dbutils.notebook.exit("NO_DATA")

# Execute based on mode with error handling
models = {}

try:
    if MODE in ["training", "both"]:
        log_debug("="*60)
        log_debug("TRAINING PHASE")
        log_debug("="*60)
        if PROPHET_AVAILABLE:
            models = run_training(burndown_df, contracts_df)
        else:
            log_debug("Skipping training - Prophet not available")

    if MODE in ["inference", "both"]:
        log_debug("="*60)
        log_debug("INFERENCE PHASE")
        log_debug("="*60)
        forecasts = run_inference(models, burndown_df, contracts_df)
        save_forecasts(forecasts)

    log_debug("="*60)
    log_debug("COMPLETE")
    log_debug("="*60)
    save_debug_log()

except Exception as e:
    log_debug(f"ERROR: {str(e)}")
    import traceback
    log_debug(traceback.format_exc())
    save_debug_log()
    raise e

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Validation & Summary

# COMMAND ----------

# Display latest forecasts
try:
    print("Latest Forecast Summary:")
    display(spark.sql(f"""
    SELECT
      f.contract_id,
      c.total_value as contract_value,
      MAX(f.forecast_date) as forecast_through,
      MAX(f.exhaustion_date_p10) as exhaustion_optimistic,
      MAX(f.exhaustion_date_p50) as exhaustion_median,
      MAX(f.exhaustion_date_p90) as exhaustion_conservative,
      MAX(f.days_to_exhaustion) as days_to_exhaustion,
      MAX(f.model_version) as model_type
    FROM {CATALOG}.{SCHEMA}.contract_forecast f
    JOIN {CATALOG}.{SCHEMA}.contracts c ON f.contract_id = c.contract_id
    GROUP BY f.contract_id, c.total_value
    """))
except Exception as e:
    print(f"Warning: Could not display forecast summary: {e}")

# COMMAND ----------

# Display model registry
try:
    print("\nModel Registry:")
    display(spark.sql(f"""
    SELECT
      contract_id,
      trained_at,
      training_points,
      ROUND(mape, 2) as mape_pct,
      ROUND(rmse, 2) as rmse,
      mlflow_run_id,
      is_active
    FROM {CATALOG}.{SCHEMA}.forecast_model_registry
    ORDER BY trained_at DESC
    """))
except Exception as e:
    print(f"Warning: Could not display model registry: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Visualization

# COMMAND ----------

def plot_forecast_for_contract(contract_id):
    """Plot historical data and forecast for a specific contract."""
    # Get historical data
    historical = burndown_df[burndown_df['contract_id'] == contract_id].copy()
    if historical.empty:
        print(f"No historical data for contract {contract_id}")
        return

    historical['usage_date'] = pd.to_datetime(historical['usage_date'])

    # Get forecast data
    forecast_df = spark.sql(f"""
        SELECT * FROM {CATALOG}.{SCHEMA}.contract_forecast
        WHERE contract_id = '{contract_id}'
        ORDER BY forecast_date
    """).toPandas()

    if forecast_df.empty:
        print(f"No forecast data for contract {contract_id}")
        return

    forecast_df['forecast_date'] = pd.to_datetime(forecast_df['forecast_date'])

    # Get contract info
    contract = contracts_df[contracts_df['contract_id'] == contract_id].iloc[0]
    contract_value = float(contract['total_value'])

    # Create figure
    fig = make_subplots(rows=1, cols=1)

    # Historical cumulative cost
    fig.add_trace(go.Scatter(
        x=historical['usage_date'],
        y=historical['cumulative_cost'],
        mode='lines',
        name='Historical Spend',
        line=dict(color='blue', width=2)
    ))

    # Forecast cumulative
    fig.add_trace(go.Scatter(
        x=forecast_df['forecast_date'],
        y=forecast_df['predicted_cumulative'],
        mode='lines',
        name='Forecast (Median)',
        line=dict(color='green', width=2, dash='dash')
    ))

    # Confidence band
    last_cumulative = float(historical['cumulative_cost'].max())
    forecast_df['cumulative_lower'] = last_cumulative + forecast_df['lower_bound'].cumsum()
    forecast_df['cumulative_upper'] = last_cumulative + forecast_df['upper_bound'].cumsum()

    fig.add_trace(go.Scatter(
        x=pd.concat([forecast_df['forecast_date'], forecast_df['forecast_date'][::-1]]),
        y=pd.concat([forecast_df['cumulative_upper'], forecast_df['cumulative_lower'][::-1]]),
        fill='toself',
        fillcolor='rgba(0,255,0,0.1)',
        line=dict(color='rgba(0,255,0,0)'),
        name='Confidence Band (80%)'
    ))

    # Contract limit line
    fig.add_hline(
        y=contract_value,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Contract Limit: ${contract_value:,.0f}"
    )

    # Exhaustion date markers
    p50_date = forecast_df['exhaustion_date_p50'].iloc[0]
    if pd.notna(p50_date):
        fig.add_vline(
            x=pd.to_datetime(p50_date),
            line_dash="dot",
            line_color="orange",
            annotation_text=f"Exhaustion (p50): {p50_date}"
        )

    fig.update_layout(
        title=f'Contract {contract_id} - Consumption Forecast',
        xaxis_title='Date',
        yaxis_title='Cumulative Cost ($)',
        height=500,
        showlegend=True
    )

    fig.show()

# Plot for first contract (skip if running in job mode without display)
try:
    if not contracts_df.empty:
        plot_forecast_for_contract(contracts_df['contract_id'].iloc[0])
except Exception as e:
    print(f"Warning: Could not create visualization: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10. Notebook Exit

# COMMAND ----------

# Return summary status
result = {
    "mode": MODE,
    "contracts_processed": len(contracts_df),
    "status": "SUCCESS"
}

dbutils.notebook.exit(str(result))
