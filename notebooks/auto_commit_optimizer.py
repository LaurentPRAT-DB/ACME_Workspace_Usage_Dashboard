# Databricks notebook source
# MAGIC %md
# MAGIC # Auto-Commit Optimizer
# MAGIC ## Intelligent Contract Commitment Recommendation
# MAGIC
# MAGIC This notebook analyzes historical consumption and predicts future usage to recommend
# MAGIC the optimal contract commitment amount that:
# MAGIC - Maximizes discount (higher commitment = higher tier discount)
# MAGIC - Ensures near-100% utilization (no wasted commitment)
# MAGIC - Accounts for growth via Prophet ML forecasting
# MAGIC
# MAGIC **Default Behavior (no duration specified):**
# MAGIC - Uses 2-year contract duration
# MAGIC - First year: Historical consumption analysis
# MAGIC - Second year: Prophet ML prediction
# MAGIC
# MAGIC **Version:** 1.0.0

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Setup & Configuration

# COMMAND ----------

import datetime as dt
import traceback

DEBUG_LOG = []

# Get catalog/schema early for debug logging
dbutils.widgets.text("catalog", "main", "Unity Catalog")
dbutils.widgets.text("schema", "account_monitoring_dev", "Schema")
_DEBUG_CATALOG = dbutils.widgets.get("catalog")
_DEBUG_SCHEMA = dbutils.widgets.get("schema")

def log_debug(message):
    """Log debug message with timestamp"""
    timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    DEBUG_LOG.append(log_entry)
    print(log_entry)

def save_debug_log():
    """Save debug log to a Delta table for retrieval"""
    try:
        log_text = "\n".join(DEBUG_LOG)
        spark.sql(f"""
            CREATE TABLE IF NOT EXISTS {_DEBUG_CATALOG}.{_DEBUG_SCHEMA}.autocommit_debug_log (
                run_id STRING,
                timestamp TIMESTAMP,
                log_text STRING
            ) USING DELTA
        """)
        run_id = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        spark.sql(f"""
            INSERT INTO {_DEBUG_CATALOG}.{_DEBUG_SCHEMA}.autocommit_debug_log
            VALUES ('{run_id}', CURRENT_TIMESTAMP(), '{log_text.replace("'", "''")}')
        """)
        print(f"Debug log saved with run_id: {run_id}")
    except Exception as e:
        print(f"Failed to save debug log: {e}")

log_debug("=== AUTO-COMMIT OPTIMIZER STARTED ===")

# COMMAND ----------

# Widget parameters
try:
    log_debug("Setting up widgets...")
    # Duration: empty means auto-detect (default 2 years)
    dbutils.widgets.text("duration_years", "", "Duration (years, empty=auto)")
    dbutils.widgets.text("start_date", "", "Contract Start (YYYY-MM-DD, empty=today)")
    dbutils.widgets.text("target_utilization", "95", "Target Utilization (%)")
    dbutils.widgets.text("historical_days", "365", "Historical Lookback (days)")
    dbutils.widgets.text("account_id", "", "Account ID (empty=auto)")
    log_debug("Widgets created successfully")
except Exception as e:
    log_debug(f"Error creating widgets: {e}")

# Get widget values
try:
    CATALOG = dbutils.widgets.get("catalog")
    SCHEMA = dbutils.widgets.get("schema")

    # Duration: default to 2 years if not specified
    duration_str = dbutils.widgets.get("duration_years").strip()
    DURATION_YEARS = int(duration_str) if duration_str else 2

    # Start date: default to today
    start_str = dbutils.widgets.get("start_date").strip()
    if start_str:
        CONTRACT_START = dt.datetime.strptime(start_str, "%Y-%m-%d").date()
    else:
        CONTRACT_START = dt.date.today()

    TARGET_UTILIZATION = float(dbutils.widgets.get("target_utilization")) / 100.0
    HISTORICAL_DAYS = int(dbutils.widgets.get("historical_days"))

    # Account ID: auto-detect if not specified
    account_str = dbutils.widgets.get("account_id").strip()
    ACCOUNT_ID = account_str if account_str else None

    log_debug(f"Configuration:")
    log_debug(f"  Catalog: {CATALOG}")
    log_debug(f"  Schema: {SCHEMA}")
    log_debug(f"  Duration: {DURATION_YEARS} years")
    log_debug(f"  Contract Start: {CONTRACT_START}")
    log_debug(f"  Target Utilization: {TARGET_UTILIZATION*100:.0f}%")
    log_debug(f"  Historical Days: {HISTORICAL_DAYS}")
    log_debug(f"  Account ID: {ACCOUNT_ID or 'auto-detect'}")
except Exception as e:
    log_debug(f"Error getting widget values: {e}")
    raise

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
    from decimal import Decimal
    log_debug("Standard imports successful")
except Exception as e:
    log_debug(f"Error in standard imports: {e}")
    save_debug_log()
    raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Data Loading

# COMMAND ----------

def get_account_id():
    """Get account_id from system.billing.usage if not specified."""
    global ACCOUNT_ID
    if ACCOUNT_ID:
        return ACCOUNT_ID

    result = spark.sql("""
        SELECT DISTINCT account_id
        FROM system.billing.usage
        LIMIT 1
    """).collect()

    if result:
        ACCOUNT_ID = result[0]['account_id']
        log_debug(f"Auto-detected account_id: {ACCOUNT_ID}")
        return ACCOUNT_ID

    raise ValueError("Could not determine account_id")

def load_historical_consumption(account_id, lookback_days):
    """Load historical daily consumption from system.billing.usage."""
    query = f"""
    SELECT
      usage_date,
      SUM(usage_quantity * pricing.default) as daily_cost
    FROM system.billing.usage
    WHERE account_id = '{account_id}'
      AND usage_date >= DATE_SUB(CURRENT_DATE(), {lookback_days})
      AND usage_date < CURRENT_DATE()
    GROUP BY usage_date
    ORDER BY usage_date
    """
    return spark.sql(query).toPandas()

def load_discount_tiers(duration_years):
    """Load applicable discount tiers for the given duration."""
    # Get tiers for this duration and nearby durations
    query = f"""
    SELECT
      tier_id,
      tier_name,
      min_commitment,
      max_commitment,
      duration_years,
      discount_rate
    FROM {CATALOG}.{SCHEMA}.discount_tiers
    WHERE duration_years = {duration_years}
      AND (effective_date IS NULL OR effective_date <= CURRENT_DATE())
      AND (expiration_date IS NULL OR expiration_date > CURRENT_DATE())
    ORDER BY min_commitment ASC
    """
    return spark.sql(query).toPandas()

# Load data
log_debug("Loading data...")
try:
    account_id = get_account_id()
    historical_df = load_historical_consumption(account_id, HISTORICAL_DAYS)
    log_debug(f"Loaded {len(historical_df)} days of historical data")

    if not historical_df.empty:
        log_debug(f"  Date range: {historical_df['usage_date'].min()} to {historical_df['usage_date'].max()}")
        log_debug(f"  Total consumption: ${historical_df['daily_cost'].sum():,.2f}")

    discount_tiers_df = load_discount_tiers(DURATION_YEARS)
    log_debug(f"Loaded {len(discount_tiers_df)} discount tiers for {DURATION_YEARS}-year contracts")
except Exception as e:
    log_debug(f"Error loading data: {e}")
    save_debug_log()
    raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Consumption Analysis

# COMMAND ----------

def analyze_historical_consumption(df):
    """Analyze historical consumption patterns."""
    if df.empty:
        return {
            'daily_avg': 0,
            'daily_std': 0,
            'total': 0,
            'days': 0,
            'trend': 0  # Daily growth rate
        }

    # Convert to float to avoid Decimal issues
    df = df.copy()
    df['daily_cost'] = df['daily_cost'].astype(float)

    # Basic stats
    daily_avg = df['daily_cost'].mean()
    daily_std = df['daily_cost'].std()
    total = df['daily_cost'].sum()
    days = len(df)

    # Calculate trend (simple linear regression)
    if days > 7:
        x = np.arange(days)
        y = df['daily_cost'].values
        # Remove NaN/inf values
        mask = np.isfinite(y)
        if mask.sum() > 2:
            slope, _ = np.polyfit(x[mask], y[mask], 1)
            trend = slope  # Daily change
        else:
            trend = 0
    else:
        trend = 0

    return {
        'daily_avg': daily_avg,
        'daily_std': daily_std,
        'total': total,
        'days': days,
        'trend': trend
    }

# Analyze historical data
log_debug("Analyzing historical consumption...")
historical_stats = analyze_historical_consumption(historical_df)
log_debug(f"  Daily average: ${historical_stats['daily_avg']:,.2f}")
log_debug(f"  Daily std dev: ${historical_stats['daily_std']:,.2f}")
log_debug(f"  Total ({historical_stats['days']} days): ${historical_stats['total']:,.2f}")
log_debug(f"  Daily trend: ${historical_stats['trend']:,.2f}/day")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Prophet Forecasting

# COMMAND ----------

def prepare_prophet_data(df):
    """Prepare data for Prophet (ds, y format)."""
    if df.empty:
        return None

    prophet_df = pd.DataFrame({
        'ds': pd.to_datetime(df['usage_date']),
        'y': df['daily_cost'].astype(float)
    })

    # Sort and fill gaps
    prophet_df = prophet_df.sort_values('ds').reset_index(drop=True)

    if len(prophet_df) > 1:
        date_range = pd.date_range(start=prophet_df['ds'].min(), end=prophet_df['ds'].max())
        prophet_df = prophet_df.set_index('ds').reindex(date_range).fillna(0).reset_index()
        prophet_df.columns = ['ds', 'y']

    return prophet_df

def train_prophet_and_forecast(df, forecast_days, interval_width=0.80):
    """Train Prophet model and generate forecast."""
    if not PROPHET_AVAILABLE:
        return None, None, "Prophet not available"

    prophet_df = prepare_prophet_data(df)

    if prophet_df is None or len(prophet_df) < 30:
        return None, None, f"Insufficient data: {len(prophet_df) if prophet_df is not None else 0} days (need 30)"

    try:
        # Initialize Prophet
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            seasonality_mode='multiplicative',
            interval_width=interval_width,
            changepoint_prior_scale=0.05
        )

        # Add monthly seasonality
        model.add_seasonality(name='monthly', period=30.5, fourier_order=5)

        # Fit model
        model.fit(prophet_df)

        # Generate future dates
        future = model.make_future_dataframe(periods=forecast_days)
        forecast = model.predict(future)

        # Filter to future only
        last_historical = prophet_df['ds'].max()
        future_forecast = forecast[forecast['ds'] > last_historical].copy()

        # Ensure non-negative predictions
        future_forecast['yhat'] = future_forecast['yhat'].clip(lower=0)
        future_forecast['yhat_lower'] = future_forecast['yhat_lower'].clip(lower=0)
        future_forecast['yhat_upper'] = future_forecast['yhat_upper'].clip(lower=0)

        return model, future_forecast, None

    except Exception as e:
        return None, None, f"Prophet training failed: {str(e)}"

def linear_forecast(historical_stats, forecast_days):
    """Fallback linear projection when Prophet unavailable."""
    daily_avg = historical_stats['daily_avg']
    trend = historical_stats['trend']
    std = historical_stats['daily_std']

    # Project with trend
    dates = pd.date_range(start=dt.date.today() + timedelta(days=1), periods=forecast_days)

    forecast_values = []
    for i, d in enumerate(dates):
        # Base value + trend
        value = daily_avg + (trend * i)
        forecast_values.append(max(0, value))  # No negative

    forecast_df = pd.DataFrame({
        'ds': dates,
        'yhat': forecast_values,
        'yhat_lower': [max(0, v - std) for v in forecast_values],
        'yhat_upper': [v + std for v in forecast_values]
    })

    return forecast_df

# COMMAND ----------

# Calculate forecast period
# Contract duration minus historical data already available
contract_end = CONTRACT_START + timedelta(days=DURATION_YEARS * 365)
today = dt.date.today()

# Historical portion of contract (from start to today or from historical data)
if CONTRACT_START < today:
    historical_contract_days = (today - CONTRACT_START).days
    forecast_days = (contract_end - today).days
else:
    # Future contract - forecast entire duration
    historical_contract_days = 0
    forecast_days = DURATION_YEARS * 365

log_debug(f"\nContract period: {CONTRACT_START} to {contract_end}")
log_debug(f"  Historical days in contract: {historical_contract_days}")
log_debug(f"  Forecast days needed: {forecast_days}")

# Generate forecast
log_debug("\nGenerating consumption forecast...")
model_used = "linear_fallback"
confidence_level = 0.5

if PROPHET_AVAILABLE and len(historical_df) >= 30:
    model, forecast_df, error = train_prophet_and_forecast(historical_df, forecast_days)
    if error:
        log_debug(f"  Prophet error: {error}")
        log_debug("  Falling back to linear projection")
        forecast_df = linear_forecast(historical_stats, forecast_days)
    else:
        model_used = "prophet"
        confidence_level = 0.8
        log_debug("  Prophet forecast generated successfully")
else:
    log_debug("  Using linear projection")
    forecast_df = linear_forecast(historical_stats, forecast_days)

log_debug(f"  Model used: {model_used}")
log_debug(f"  Forecast days: {len(forecast_df) if forecast_df is not None else 0}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Calculate Projected Consumption

# COMMAND ----------

def calculate_projected_consumption(historical_df, historical_stats, forecast_df, contract_start, contract_end):
    """
    Calculate total projected consumption over the contract period.

    Returns dict with:
    - historical_total: Consumption from historical data within contract period
    - forecasted_total: Forecasted consumption for remaining period
    - projected_total: Combined total
    - forecasted_daily_avg: Average daily forecast
    """
    today = dt.date.today()

    # Historical consumption within contract period
    if not historical_df.empty:
        hist_df = historical_df.copy()
        hist_df['usage_date'] = pd.to_datetime(hist_df['usage_date']).dt.date

        # Filter to contract period
        contract_historical = hist_df[
            (hist_df['usage_date'] >= contract_start) &
            (hist_df['usage_date'] <= min(today, contract_end))
        ]
        historical_total = float(contract_historical['daily_cost'].sum()) if not contract_historical.empty else 0

        # If contract started before our historical data, estimate missing days
        if contract_start < hist_df['usage_date'].min():
            missing_days = (hist_df['usage_date'].min() - contract_start).days
            historical_total += missing_days * historical_stats['daily_avg']
    else:
        historical_total = 0

    # Forecasted consumption
    if forecast_df is not None and not forecast_df.empty:
        forecasted_total = float(forecast_df['yhat'].sum())
        forecasted_daily_avg = float(forecast_df['yhat'].mean())
        forecast_lower = float(forecast_df['yhat_lower'].sum())
        forecast_upper = float(forecast_df['yhat_upper'].sum())
    else:
        # Use historical average for forecast period
        forecast_days = max(0, (contract_end - today).days)
        forecasted_total = forecast_days * historical_stats['daily_avg']
        forecasted_daily_avg = historical_stats['daily_avg']
        forecast_lower = forecasted_total * 0.8
        forecast_upper = forecasted_total * 1.2

    projected_total = historical_total + forecasted_total

    return {
        'historical_total': historical_total,
        'forecasted_total': forecasted_total,
        'projected_total': projected_total,
        'forecasted_daily_avg': forecasted_daily_avg,
        'forecast_lower': forecast_lower,
        'forecast_upper': forecast_upper,
        'projected_lower': historical_total + forecast_lower,
        'projected_upper': historical_total + forecast_upper
    }

# Calculate projections
projections = calculate_projected_consumption(
    historical_df, historical_stats, forecast_df, CONTRACT_START, contract_end
)

log_debug(f"\nProjected Consumption:")
log_debug(f"  Historical (in contract): ${projections['historical_total']:,.2f}")
log_debug(f"  Forecasted: ${projections['forecasted_total']:,.2f}")
log_debug(f"  Total Projected: ${projections['projected_total']:,.2f}")
log_debug(f"  Range: ${projections['projected_lower']:,.2f} - ${projections['projected_upper']:,.2f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Find Optimal Commitment

# COMMAND ----------

def find_best_discount_tier(commitment_amount, tiers_df):
    """Find the best discount tier for a given commitment amount."""
    if tiers_df.empty:
        return None, 0.0, "No tier"

    # Convert to float for comparison
    commitment = float(commitment_amount)

    # Find matching tier (highest that this commitment qualifies for)
    matching_tiers = tiers_df[tiers_df['min_commitment'] <= commitment].copy()

    if matching_tiers.empty:
        # Below minimum tier - no discount
        return None, 0.0, "Below minimum"

    # Filter out tiers where commitment exceeds max (if max is defined)
    for idx in matching_tiers.index:
        max_comm = matching_tiers.loc[idx, 'max_commitment']
        if pd.notna(max_comm) and commitment > float(max_comm):
            matching_tiers = matching_tiers.drop(idx)

    if matching_tiers.empty:
        # Above all tiers - use highest tier
        best_tier = tiers_df.loc[tiers_df['discount_rate'].idxmax()]
    else:
        # Get tier with highest discount rate
        best_tier = matching_tiers.loc[matching_tiers['discount_rate'].idxmax()]

    return best_tier['tier_id'], float(best_tier['discount_rate']), best_tier['tier_name']

def calculate_scenario(commitment, projected_consumption, discount_rate, list_price_total):
    """Calculate metrics for a commitment scenario."""
    utilization = projected_consumption / commitment if commitment > 0 else 0
    effective_cost = min(commitment, projected_consumption) * (1 - discount_rate)

    # If consumption exceeds commitment, overage is at list price
    if projected_consumption > commitment:
        overage = projected_consumption - commitment
        effective_cost += overage  # Overage at list price (no discount)

    waste = max(0, commitment - projected_consumption)
    waste_cost = waste * (1 - discount_rate)  # Money spent on unused commitment

    savings_vs_list = list_price_total - effective_cost

    # Net benefit = savings minus wasted commitment cost
    net_benefit = savings_vs_list - waste_cost

    # ROI score: maximize savings while minimizing waste
    # Higher is better
    if commitment > 0:
        roi_score = (net_benefit / commitment) * 100
    else:
        roi_score = 0

    return {
        'utilization': utilization,
        'effective_cost': effective_cost,
        'savings_vs_list': savings_vs_list,
        'waste_amount': waste,
        'waste_cost': waste_cost,
        'net_benefit': net_benefit,
        'roi_score': roi_score
    }

def find_optimal_commitment(projections, tiers_df, target_utilization=0.95):
    """
    Find the optimal commitment amount.

    Strategy:
    1. Calculate commitment needed for target utilization
    2. Find which tier that falls into
    3. Compare scenarios at tier boundaries for best ROI
    """
    projected_total = projections['projected_total']
    projected_upper = projections['projected_upper']
    list_price_total = projected_total  # At list price = consumption

    if tiers_df.empty:
        log_debug("  No discount tiers available")
        return None, []

    # Generate commitment candidates:
    # 1. Target utilization commitment
    # 2. Each tier boundary
    # 3. Conservative (higher utilization) and aggressive (lower utilization)

    candidates = []

    # Target utilization commitment
    target_commitment = projected_total / target_utilization
    candidates.append(('target', target_commitment))

    # Conservative: 100% utilization (commitment = projected)
    candidates.append(('conservative', projected_total))

    # Upper bound: 90% utilization of upper projection
    candidates.append(('aggressive', projected_upper / 0.90))

    # Tier boundaries - each min_commitment
    for _, tier in tiers_df.iterrows():
        min_comm = float(tier['min_commitment'])
        if min_comm > 0:
            candidates.append(('tier_boundary', min_comm))
        # Also try just above tier boundary
        if min_comm > 0:
            candidates.append(('tier_boundary', min_comm * 1.01))

    # Evaluate each candidate
    scenarios = []
    for candidate_type, commitment in candidates:
        if commitment <= 0:
            continue

        tier_id, discount_rate, tier_name = find_best_discount_tier(commitment, tiers_df)

        scenario = calculate_scenario(
            commitment, projected_total, discount_rate, list_price_total
        )

        scenarios.append({
            'candidate_type': candidate_type,
            'commitment': commitment,
            'tier_id': tier_id,
            'tier_name': tier_name,
            'discount_rate': discount_rate,
            **scenario
        })

    if not scenarios:
        return None, []

    # Find optimal: highest net_benefit with utilization >= target
    valid_scenarios = [s for s in scenarios if s['utilization'] >= target_utilization * 0.9]

    if valid_scenarios:
        # Sort by net_benefit descending
        valid_scenarios.sort(key=lambda x: x['net_benefit'], reverse=True)
        optimal = valid_scenarios[0]
    else:
        # Fall back to highest ROI score
        scenarios.sort(key=lambda x: x['roi_score'], reverse=True)
        optimal = scenarios[0]

    return optimal, scenarios

# Find optimal commitment
log_debug("\nFinding optimal commitment...")
optimal, all_scenarios = find_optimal_commitment(projections, discount_tiers_df, TARGET_UTILIZATION)

if optimal:
    log_debug(f"\n{'='*60}")
    log_debug(f"OPTIMAL RECOMMENDATION")
    log_debug(f"{'='*60}")
    log_debug(f"  Commitment: ${optimal['commitment']:,.2f}")
    log_debug(f"  Discount Tier: {optimal['tier_name']} ({optimal['discount_rate']*100:.0f}%)")
    log_debug(f"  Expected Utilization: {optimal['utilization']*100:.1f}%")
    log_debug(f"  Savings vs List: ${optimal['savings_vs_list']:,.2f}")
    log_debug(f"  Net Benefit: ${optimal['net_benefit']:,.2f}")
    log_debug(f"  ROI Score: {optimal['roi_score']:.2f}")
else:
    log_debug("  No optimal commitment found")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Generate Alternative Recommendations

# COMMAND ----------

def find_alternatives(optimal, all_scenarios, target_utilization):
    """Find conservative and aggressive alternatives."""
    if not optimal or not all_scenarios:
        return None, None

    optimal_commitment = optimal['commitment']

    # Conservative: Lower commitment, higher utilization
    conservative_candidates = [
        s for s in all_scenarios
        if s['commitment'] < optimal_commitment * 0.95
        and s['utilization'] > optimal['utilization']
        and s['net_benefit'] > 0
    ]

    if conservative_candidates:
        # Pick one with best balance of utilization and savings
        conservative_candidates.sort(key=lambda x: x['net_benefit'], reverse=True)
        conservative = conservative_candidates[0]
    else:
        conservative = None

    # Aggressive: Higher commitment, more savings potential
    aggressive_candidates = [
        s for s in all_scenarios
        if s['commitment'] > optimal_commitment * 1.05
        and s['discount_rate'] >= optimal['discount_rate']
        and s['net_benefit'] > 0
    ]

    if aggressive_candidates:
        # Pick one with highest discount that still has positive ROI
        aggressive_candidates.sort(key=lambda x: (x['discount_rate'], x['net_benefit']), reverse=True)
        aggressive = aggressive_candidates[0]
    else:
        aggressive = None

    return conservative, aggressive

# Find alternatives
conservative, aggressive = find_alternatives(optimal, all_scenarios, TARGET_UTILIZATION)

if conservative:
    log_debug(f"\nConservative Option:")
    log_debug(f"  Commitment: ${conservative['commitment']:,.2f}")
    log_debug(f"  Utilization: {conservative['utilization']*100:.1f}%")
    log_debug(f"  Savings: ${conservative['savings_vs_list']:,.2f}")

if aggressive:
    log_debug(f"\nAggressive Option:")
    log_debug(f"  Commitment: ${aggressive['commitment']:,.2f}")
    log_debug(f"  Utilization: {aggressive['utilization']*100:.1f}%")
    log_debug(f"  Savings: ${aggressive['savings_vs_list']:,.2f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Save Recommendations

# COMMAND ----------

def is_null_or_nat(val):
    """Check if value is None, NaN, or NaT."""
    if val is None:
        return True
    if isinstance(val, float) and np.isnan(val):
        return True
    if pd.isna(val):
        return True
    return False

def safe_float(val, default=None):
    """Safely convert to float."""
    if is_null_or_nat(val):
        return default
    return float(val)

def safe_date_str(val):
    """Safely convert date to string for SQL."""
    if is_null_or_nat(val):
        return "NULL"
    if isinstance(val, str):
        return f"'{val}'"
    if isinstance(val, (dt.date, dt.datetime)):
        return f"'{val.strftime('%Y-%m-%d')}'"
    return "NULL"

def save_recommendation(optimal, conservative, aggressive, projections, historical_stats):
    """Save recommendation to database."""
    if not optimal:
        log_debug("No recommendation to save")
        return None

    recommendation_id = str(uuid.uuid4())

    # Calculate dates
    historical_start = (dt.date.today() - timedelta(days=HISTORICAL_DAYS))
    historical_end = dt.date.today()
    proposed_end = CONTRACT_START + timedelta(days=DURATION_YEARS * 365)

    # Prepare values
    conservative_commitment = safe_float(conservative['commitment']) if conservative else None
    conservative_discount = safe_float(conservative['discount_rate']) if conservative else None
    aggressive_commitment = safe_float(aggressive['commitment']) if aggressive else None
    aggressive_discount = safe_float(aggressive['discount_rate']) if aggressive else None

    # Build SQL
    insert_sql = f"""
    INSERT INTO {CATALOG}.{SCHEMA}.auto_commit_recommendations (
        recommendation_id,
        account_id,
        analysis_date,
        historical_start,
        historical_end,
        proposed_start,
        proposed_end,
        duration_years,
        historical_daily_avg,
        historical_total,
        forecasted_daily_avg,
        forecasted_total,
        projected_total,
        optimal_commitment,
        optimal_discount_rate,
        optimal_tier_name,
        optimal_utilization_pct,
        list_price_total,
        committed_price_total,
        total_savings,
        savings_pct,
        conservative_commitment,
        conservative_discount_rate,
        aggressive_commitment,
        aggressive_discount_rate,
        model_used,
        confidence_level,
        status,
        created_at,
        updated_at
    ) VALUES (
        '{recommendation_id}',
        '{ACCOUNT_ID}',
        CURRENT_DATE(),
        '{historical_start}',
        '{historical_end}',
        '{CONTRACT_START}',
        '{proposed_end}',
        {DURATION_YEARS},
        {safe_float(historical_stats['daily_avg'], 0)},
        {safe_float(projections['historical_total'], 0)},
        {safe_float(projections['forecasted_daily_avg'], 0)},
        {safe_float(projections['forecasted_total'], 0)},
        {safe_float(projections['projected_total'], 0)},
        {safe_float(optimal['commitment'], 0)},
        {safe_float(optimal['discount_rate'], 0)},
        '{optimal['tier_name'].replace("'", "''") if optimal.get('tier_name') else ''}',
        {safe_float(optimal['utilization'] * 100, 0)},
        {safe_float(projections['projected_total'], 0)},
        {safe_float(optimal['effective_cost'], 0)},
        {safe_float(optimal['savings_vs_list'], 0)},
        {safe_float(optimal['savings_vs_list'] / projections['projected_total'] * 100, 0) if projections['projected_total'] > 0 else 0},
        {conservative_commitment if conservative_commitment else 'NULL'},
        {conservative_discount if conservative_discount else 'NULL'},
        {aggressive_commitment if aggressive_commitment else 'NULL'},
        {aggressive_discount if aggressive_discount else 'NULL'},
        '{model_used}',
        {confidence_level},
        'ACTIVE',
        CURRENT_TIMESTAMP(),
        CURRENT_TIMESTAMP()
    )
    """

    spark.sql(insert_sql)
    log_debug(f"Saved recommendation: {recommendation_id}")

    return recommendation_id

def save_scenarios(recommendation_id, all_scenarios, optimal, conservative, aggressive, projections):
    """Save all analyzed scenarios."""
    if not all_scenarios:
        return

    for scenario in all_scenarios:
        scenario_id = str(uuid.uuid4())

        is_optimal = (scenario['commitment'] == optimal['commitment']) if optimal else False
        is_conservative = (scenario['commitment'] == conservative['commitment']) if conservative else False
        is_aggressive = (scenario['commitment'] == aggressive['commitment']) if aggressive else False

        # Determine risk level based on utilization variance
        util = scenario['utilization']
        if util >= 0.95:
            risk = 'LOW'
        elif util >= 0.85:
            risk = 'MEDIUM'
        else:
            risk = 'HIGH'

        insert_sql = f"""
        INSERT INTO {CATALOG}.{SCHEMA}.auto_commit_scenarios (
            scenario_id,
            recommendation_id,
            account_id,
            commitment_amount,
            duration_years,
            discount_tier_id,
            discount_tier_name,
            discount_rate,
            projected_consumption,
            effective_cost,
            utilization_pct,
            savings_vs_list,
            savings_vs_baseline,
            waste_amount,
            net_benefit,
            roi_score,
            is_optimal,
            is_conservative,
            is_aggressive,
            risk_level,
            created_at
        ) VALUES (
            '{scenario_id}',
            '{recommendation_id}',
            '{ACCOUNT_ID}',
            {safe_float(scenario['commitment'], 0)},
            {DURATION_YEARS},
            '{scenario.get('tier_id', '')}',
            '{(scenario.get('tier_name', '') or '').replace("'", "''")}',
            {safe_float(scenario['discount_rate'], 0)},
            {safe_float(projections['projected_total'], 0)},
            {safe_float(scenario['effective_cost'], 0)},
            {safe_float(scenario['utilization'] * 100, 0)},
            {safe_float(scenario['savings_vs_list'], 0)},
            {safe_float(scenario['savings_vs_list'], 0)},
            {safe_float(scenario['waste_amount'], 0)},
            {safe_float(scenario['net_benefit'], 0)},
            {safe_float(scenario['roi_score'], 0)},
            {is_optimal},
            {is_conservative},
            {is_aggressive},
            '{risk}',
            CURRENT_TIMESTAMP()
        )
        """

        spark.sql(insert_sql)

    log_debug(f"Saved {len(all_scenarios)} scenarios")

# Save to database
log_debug("\nSaving recommendations...")
try:
    recommendation_id = save_recommendation(optimal, conservative, aggressive, projections, historical_stats)
    if recommendation_id:
        save_scenarios(recommendation_id, all_scenarios, optimal, conservative, aggressive, projections)
except Exception as e:
    log_debug(f"Error saving recommendations: {e}")
    log_debug(traceback.format_exc())

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Summary & Visualization

# COMMAND ----------

# Display recommendation summary
if optimal:
    print("=" * 70)
    print("AUTO-COMMIT OPTIMIZATION RECOMMENDATION")
    print("=" * 70)
    print(f"\nAccount: {ACCOUNT_ID}")
    print(f"Contract Period: {CONTRACT_START} to {contract_end} ({DURATION_YEARS} years)")
    print(f"\n{'Analysis Summary':^70}")
    print("-" * 70)
    print(f"Historical Daily Average:     ${historical_stats['daily_avg']:>15,.2f}")
    print(f"Forecasted Daily Average:     ${projections['forecasted_daily_avg']:>15,.2f}")
    print(f"Total Projected Consumption:  ${projections['projected_total']:>15,.2f}")
    print(f"Model Used:                   {model_used:>15}")
    print(f"\n{'Optimal Recommendation':^70}")
    print("-" * 70)
    print(f"Commitment Amount:            ${optimal['commitment']:>15,.2f}")
    print(f"Discount Tier:                {optimal['tier_name']:>15}")
    print(f"Discount Rate:                {optimal['discount_rate']*100:>14.0f}%")
    print(f"Expected Utilization:         {optimal['utilization']*100:>14.1f}%")
    print(f"Total Savings vs List:        ${optimal['savings_vs_list']:>15,.2f}")
    print(f"Net Benefit:                  ${optimal['net_benefit']:>15,.2f}")

    if conservative:
        print(f"\n{'Conservative Alternative (Lower Risk)':^70}")
        print("-" * 70)
        print(f"Commitment Amount:            ${conservative['commitment']:>15,.2f}")
        print(f"Discount Rate:                {conservative['discount_rate']*100:>14.0f}%")
        print(f"Expected Utilization:         {conservative['utilization']*100:>14.1f}%")
        print(f"Savings:                      ${conservative['savings_vs_list']:>15,.2f}")

    if aggressive:
        print(f"\n{'Aggressive Alternative (Higher Savings)':^70}")
        print("-" * 70)
        print(f"Commitment Amount:            ${aggressive['commitment']:>15,.2f}")
        print(f"Discount Rate:                {aggressive['discount_rate']*100:>14.0f}%")
        print(f"Expected Utilization:         {aggressive['utilization']*100:>14.1f}%")
        print(f"Savings:                      ${aggressive['savings_vs_list']:>15,.2f}")

    print("\n" + "=" * 70)

# COMMAND ----------

# Visualization
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    if optimal and historical_df is not None and not historical_df.empty:
        # Create figure with subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Daily Consumption Over Time',
                'Commitment Scenarios Comparison',
                'Cumulative Consumption Projection',
                'Savings by Commitment Level'
            ),
            specs=[[{"type": "scatter"}, {"type": "bar"}],
                   [{"type": "scatter"}, {"type": "scatter"}]]
        )

        # 1. Daily consumption timeline
        hist_df = historical_df.copy()
        hist_df['usage_date'] = pd.to_datetime(hist_df['usage_date'])

        fig.add_trace(
            go.Scatter(
                x=hist_df['usage_date'],
                y=hist_df['daily_cost'],
                mode='lines',
                name='Historical',
                line=dict(color='blue')
            ),
            row=1, col=1
        )

        if forecast_df is not None:
            fig.add_trace(
                go.Scatter(
                    x=forecast_df['ds'],
                    y=forecast_df['yhat'],
                    mode='lines',
                    name='Forecast',
                    line=dict(color='green', dash='dash')
                ),
                row=1, col=1
            )

        # 2. Scenario comparison bar chart
        scenario_names = ['Optimal']
        scenario_values = [optimal['commitment']]
        scenario_savings = [optimal['savings_vs_list']]

        if conservative:
            scenario_names.append('Conservative')
            scenario_values.append(conservative['commitment'])
            scenario_savings.append(conservative['savings_vs_list'])

        if aggressive:
            scenario_names.append('Aggressive')
            scenario_values.append(aggressive['commitment'])
            scenario_savings.append(aggressive['savings_vs_list'])

        fig.add_trace(
            go.Bar(
                x=scenario_names,
                y=scenario_values,
                name='Commitment',
                marker_color='steelblue'
            ),
            row=1, col=2
        )

        # 3. Cumulative projection
        # Historical cumulative
        hist_df['cumulative'] = hist_df['daily_cost'].cumsum()
        fig.add_trace(
            go.Scatter(
                x=hist_df['usage_date'],
                y=hist_df['cumulative'],
                mode='lines',
                name='Historical Cumulative',
                line=dict(color='blue')
            ),
            row=2, col=1
        )

        # Commitment line
        fig.add_hline(
            y=optimal['commitment'],
            line_dash="dash",
            line_color="red",
            annotation_text=f"Optimal: ${optimal['commitment']:,.0f}",
            row=2, col=1
        )

        # 4. Savings by commitment level
        if all_scenarios:
            commitments = [s['commitment'] for s in all_scenarios]
            savings = [s['savings_vs_list'] for s in all_scenarios]

            fig.add_trace(
                go.Scatter(
                    x=commitments,
                    y=savings,
                    mode='markers',
                    name='Scenarios',
                    marker=dict(size=8, color='purple')
                ),
                row=2, col=2
            )

            # Mark optimal
            fig.add_trace(
                go.Scatter(
                    x=[optimal['commitment']],
                    y=[optimal['savings_vs_list']],
                    mode='markers',
                    name='Optimal',
                    marker=dict(size=15, color='red', symbol='star')
                ),
                row=2, col=2
            )

        fig.update_layout(
            height=800,
            title_text=f"Auto-Commit Optimization Analysis - {ACCOUNT_ID}",
            showlegend=True
        )

        fig.show()

except Exception as e:
    log_debug(f"Visualization error: {e}")
    print(f"Could not generate visualization: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10. Notebook Exit

# COMMAND ----------

# Save debug log
save_debug_log()

# Return summary
result = {
    "account_id": ACCOUNT_ID,
    "duration_years": DURATION_YEARS,
    "optimal_commitment": optimal['commitment'] if optimal else None,
    "optimal_discount": optimal['discount_rate'] if optimal else None,
    "projected_consumption": projections['projected_total'],
    "model_used": model_used,
    "status": "SUCCESS" if optimal else "NO_RECOMMENDATION"
}

print(f"\nResult: {result}")
dbutils.notebook.exit(str(result))
