# Databricks notebook source
# MAGIC %md
# MAGIC # What-If Discount Simulator
# MAGIC ## Scenario-Based Contract Savings Analysis
# MAGIC
# MAGIC This notebook generates what-if discount scenarios and calculates potential savings
# MAGIC for Databricks commit contracts.
# MAGIC
# MAGIC **Features:**
# MAGIC - Duration-aware discount scenarios (longer contracts = higher max discount)
# MAGIC - Tier-based discount lookup from discount_tiers table
# MAGIC - Simulated burndown with discount applied
# MAGIC - Scaled Prophet forecasts for exhaustion prediction
# MAGIC - Break-even analysis and sweet spot detection
# MAGIC - "What if longer duration" analysis showing incentive to extend
# MAGIC
# MAGIC **Version:** 1.1.0

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Setup & Configuration

# COMMAND ----------

import datetime as dt
import traceback

DEBUG_LOG = []

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
            CREATE TABLE IF NOT EXISTS main.account_monitoring_dev.whatif_debug_log (
                run_id STRING,
                timestamp TIMESTAMP,
                log_text STRING
            ) USING DELTA
        """)
        run_id = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        # Escape single quotes in log text
        escaped_log = log_text.replace("'", "''")
        spark.sql(f"""
            INSERT INTO main.account_monitoring_dev.whatif_debug_log
            VALUES ('{run_id}', CURRENT_TIMESTAMP(), '{escaped_log}')
        """)
        print(f"Debug log saved with run_id: {run_id}")
    except Exception as e:
        print(f"Failed to save debug log: {str(e)}")

log_debug("=== WHAT-IF SIMULATOR STARTED ===")

# COMMAND ----------

# Standard imports
from pyspark.sql import functions as F
from pyspark.sql.types import *
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid

log_debug("Imports successful")

# Configuration
CATALOG = "main"
SCHEMA = "account_monitoring_dev"

# Base discount levels to simulate (will be capped by tier max)
BASE_DISCOUNT_LEVELS = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0]

# Sweet spot threshold - minimum utilization to consider a scenario viable
SWEET_SPOT_MIN_UTILIZATION = 85.0

# Discount step size for scenarios (percentage points)
DISCOUNT_STEP = 5.0

log_debug(f"Catalog: {CATALOG}, Schema: {SCHEMA}")
log_debug(f"Base discount levels: {BASE_DISCOUNT_LEVELS}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Data Loading

# COMMAND ----------

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

def load_contract_burndown():
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

def load_contract_forecasts():
    """Load Prophet forecasts from contract_forecast table."""
    query = f"""
    SELECT
      contract_id,
      forecast_date,
      model_version,
      predicted_daily_cost,
      predicted_cumulative,
      lower_bound,
      upper_bound,
      exhaustion_date_p10,
      exhaustion_date_p50,
      exhaustion_date_p90,
      days_to_exhaustion
    FROM {CATALOG}.{SCHEMA}.contract_forecast
    ORDER BY contract_id, forecast_date
    """
    return spark.sql(query).toPandas()

def is_null_or_nat(val):
    """Check if value is None, NaN, or NaT (pandas null types)."""
    if val is None:
        return True
    if pd.isna(val):
        return True
    return False

def safe_date_str(val):
    """Convert date to SQL-safe string or NULL."""
    if is_null_or_nat(val):
        return 'NULL'
    return f"'{val}'"

def load_discount_tiers():
    """Load discount tier configuration."""
    query = f"""
    SELECT
      tier_id,
      tier_name,
      min_commitment,
      max_commitment,
      duration_years,
      discount_rate
    FROM {CATALOG}.{SCHEMA}.discount_tiers
    WHERE (effective_date IS NULL OR effective_date <= CURRENT_DATE())
      AND (expiration_date IS NULL OR expiration_date >= CURRENT_DATE())
    ORDER BY min_commitment, duration_years
    """
    return spark.sql(query).toPandas()

def get_max_discount_for_contract(commitment_amount, duration_years, tiers_df):
    """
    Look up the maximum discount available for a given commitment and duration.

    Args:
        commitment_amount: Contract value in dollars
        duration_years: Contract duration (1, 2, or 3)
        tiers_df: Discount tiers DataFrame

    Returns:
        Maximum discount rate as percentage (e.g., 15.0 for 15%)
    """
    # Filter tiers for matching commitment range and duration
    matching_tiers = tiers_df[
        (tiers_df['min_commitment'] <= commitment_amount) &
        ((tiers_df['max_commitment'].isna()) | (tiers_df['max_commitment'] >= commitment_amount)) &
        (tiers_df['duration_years'] == duration_years)
    ]

    if matching_tiers.empty:
        # No matching tier - return a conservative default
        log_debug(f"  No tier found for ${commitment_amount:,.0f} / {duration_years}yr, using 5% default")
        return 5.0

    # Get the discount rate (convert from decimal to percentage)
    max_discount = float(matching_tiers['discount_rate'].max()) * 100
    return max_discount

def get_discount_by_duration(commitment_amount, tiers_df):
    """
    Get max discount available for each duration (1, 2, 3 years).
    Shows the incentive of longer commitments.

    Returns:
        Dict mapping duration_years to max_discount_pct
    """
    discounts = {}
    for duration in [1, 2, 3]:
        discounts[duration] = get_max_discount_for_contract(commitment_amount, duration, tiers_df)
    return discounts

def calculate_contract_duration_years(start_date, end_date):
    """Calculate contract duration in years (rounded to nearest integer)."""
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    days = (end - start).days
    years = round(days / 365)
    return max(1, min(years, 3))  # Clamp to 1-3 years

# Load data
try:
    log_debug("Loading contracts...")
    contracts_df = load_active_contracts()
    log_debug(f"Loaded {len(contracts_df)} active contracts")
except Exception as e:
    log_debug(f"ERROR loading contracts: {str(e)}")
    log_debug(f"Stack trace: {traceback.format_exc()}")
    save_debug_log()
    raise

try:
    log_debug("Loading burndown data...")
    burndown_df = load_contract_burndown()
    log_debug(f"Loaded {len(burndown_df)} burndown records")
except Exception as e:
    log_debug(f"ERROR loading burndown: {str(e)}")
    log_debug(f"Stack trace: {traceback.format_exc()}")
    save_debug_log()
    raise

try:
    log_debug("Loading forecast data...")
    forecast_df = load_contract_forecasts()
    log_debug(f"Loaded {len(forecast_df)} forecast records")
except Exception as e:
    log_debug(f"ERROR loading forecasts: {str(e)}")
    log_debug(f"Stack trace: {traceback.format_exc()}")
    save_debug_log()
    raise

try:
    log_debug("Loading discount tiers...")
    tiers_df = load_discount_tiers()
    log_debug(f"Loaded {len(tiers_df)} discount tiers")
except Exception as e:
    log_debug(f"ERROR loading tiers: {str(e)}")
    log_debug(f"Stack trace: {traceback.format_exc()}")
    save_debug_log()
    raise

# Save debug log after data loading
log_debug("Data loading complete - saving checkpoint log")
save_debug_log()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Scenario Generation

# COMMAND ----------

def generate_scenarios_for_contract(contract_id, contract_value, start_date, end_date, tiers_df):
    """
    Generate discount scenarios for a contract, capped by duration-based tier max.

    Longer contracts unlock higher max discounts, incentivizing extended commitments.

    Args:
        contract_id: Contract identifier
        contract_value: Total contract value
        start_date: Contract start date
        end_date: Contract end date
        tiers_df: Discount tiers DataFrame

    Returns:
        List of scenario dictionaries
    """
    scenarios = []

    # Calculate contract duration
    duration_years = calculate_contract_duration_years(start_date, end_date)

    # Get max discount for current duration
    max_discount_current = get_max_discount_for_contract(contract_value, duration_years, tiers_df)

    # Get discounts available for all durations (for comparison)
    discounts_by_duration = get_discount_by_duration(contract_value, tiers_df)

    log_debug(f"  Contract duration: {duration_years} years")
    log_debug(f"  Max discount for current duration: {max_discount_current}%")
    log_debug(f"  Discounts by duration: {discounts_by_duration}")

    # Generate scenarios from 0% up to max for current duration
    discount_levels = [0.0]
    current_discount = DISCOUNT_STEP
    while current_discount <= max_discount_current:
        discount_levels.append(current_discount)
        current_discount += DISCOUNT_STEP

    # Ensure max discount is included if not already
    if max_discount_current not in discount_levels:
        discount_levels.append(max_discount_current)

    discount_levels = sorted(set(discount_levels))

    for discount_pct in discount_levels:
        scenario_id = str(uuid.uuid4())
        is_baseline = (discount_pct == 0.0)

        # Scenario naming
        if is_baseline:
            scenario_name = "Baseline (No Discount)"
            description = "Current consumption without any discount"
        elif discount_pct == max_discount_current:
            scenario_name = f"{discount_pct:.0f}% Discount (Max for {duration_years}yr)"
            description = f"Maximum discount available for {duration_years}-year commitment at ${contract_value:,.0f}"
        else:
            scenario_name = f"{discount_pct:.0f}% Discount"
            description = f"What-if scenario with {discount_pct}% discount applied"

        scenarios.append({
            'scenario_id': scenario_id,
            'contract_id': contract_id,
            'scenario_name': scenario_name,
            'description': description,
            'discount_pct': discount_pct,
            'discount_type': 'overall',
            'adjusted_total_value': float(contract_value),
            'adjusted_start_date': None,
            'adjusted_end_date': None,
            'is_baseline': is_baseline,
            'is_recommended': False,
            'is_max_for_duration': (discount_pct == max_discount_current),
            'contract_duration_years': duration_years,
            'status': 'ACTIVE',
            'created_by': 'whatif_simulator',
            'created_at': datetime.now(),
            'updated_at': None
        })

    # Add "what if longer duration" scenarios to show incentive
    for longer_duration in [2, 3]:
        if longer_duration > duration_years:
            longer_max = discounts_by_duration.get(longer_duration, 0)
            if longer_max > max_discount_current:
                scenario_id = str(uuid.uuid4())
                extra_discount = longer_max - max_discount_current

                scenarios.append({
                    'scenario_id': scenario_id,
                    'contract_id': contract_id,
                    'scenario_name': f"{longer_max:.0f}% (If {longer_duration}yr commit)",
                    'description': f"Potential discount if contract extended to {longer_duration} years (+{extra_discount:.0f}% vs current)",
                    'discount_pct': longer_max,
                    'discount_type': 'overall',
                    'adjusted_total_value': float(contract_value),
                    'adjusted_start_date': None,
                    'adjusted_end_date': None,
                    'is_baseline': False,
                    'is_recommended': False,
                    'is_max_for_duration': True,
                    'is_longer_duration_scenario': True,
                    'potential_duration_years': longer_duration,
                    'contract_duration_years': duration_years,
                    'status': 'ACTIVE',
                    'created_by': 'whatif_simulator',
                    'created_at': datetime.now(),
                    'updated_at': None
                })

    return scenarios

# Generate scenarios for all contracts
log_debug("Generating scenarios for all contracts...")
all_scenarios = []

for _, contract in contracts_df.iterrows():
    log_debug(f"Contract {contract['contract_id']}: ${float(contract['total_value']):,.0f}")
    contract_scenarios = generate_scenarios_for_contract(
        contract['contract_id'],
        contract['total_value'],
        contract['start_date'],
        contract['end_date'],
        tiers_df
    )
    all_scenarios.extend(contract_scenarios)
    log_debug(f"  Generated {len(contract_scenarios)} scenarios")

log_debug(f"Total scenarios generated: {len(all_scenarios)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Scenario Burndown Calculation

# COMMAND ----------

def calculate_scenario_burndown(contract_id, scenario_id, discount_pct, burndown_data, contract_value):
    """
    Calculate simulated burndown with discount applied.

    Args:
        contract_id: Contract identifier
        scenario_id: Scenario identifier
        discount_pct: Discount percentage (0-100)
        burndown_data: Historical burndown DataFrame
        contract_value: Contract commitment value

    Returns:
        List of burndown records for this scenario
    """
    contract_burndown = burndown_data[burndown_data['contract_id'] == contract_id].copy()

    if contract_burndown.empty:
        return []

    discount_factor = 1 - (discount_pct / 100)
    records = []

    cumulative_savings = 0.0
    simulated_cumulative = 0.0

    for _, row in contract_burndown.iterrows():
        original_daily = float(row['daily_cost']) if pd.notna(row['daily_cost']) else 0.0
        original_cumulative = float(row['cumulative_cost']) if pd.notna(row['cumulative_cost']) else 0.0

        # Apply discount
        simulated_daily = original_daily * discount_factor
        simulated_cumulative += simulated_daily

        # Calculate savings
        daily_savings = original_daily - simulated_daily
        cumulative_savings += daily_savings

        records.append({
            'scenario_id': scenario_id,
            'contract_id': contract_id,
            'usage_date': row['usage_date'],
            'original_daily_cost': original_daily,
            'original_cumulative': original_cumulative,
            'simulated_daily_cost': simulated_daily,
            'simulated_cumulative': simulated_cumulative,
            'scenario_commitment': contract_value,
            'simulated_remaining': contract_value - simulated_cumulative,
            'daily_savings': daily_savings,
            'cumulative_savings': cumulative_savings,
            'calculated_at': datetime.now()
        })

    return records

# Calculate burndown for all scenarios
log_debug("Calculating scenario burndown...")
all_burndown = []

for scenario in all_scenarios:
    contract = contracts_df[contracts_df['contract_id'] == scenario['contract_id']].iloc[0]
    burndown_records = calculate_scenario_burndown(
        scenario['contract_id'],
        scenario['scenario_id'],
        scenario['discount_pct'],
        burndown_df,
        float(contract['total_value'])
    )
    all_burndown.extend(burndown_records)

log_debug(f"Total burndown records: {len(all_burndown)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Scenario Forecast Calculation

# COMMAND ----------

def calculate_scenario_forecast(contract_id, scenario_id, discount_pct, forecast_data, contract_value, baseline_exhaustion_date):
    """
    Calculate scaled forecast with discount and new exhaustion dates.

    Args:
        contract_id: Contract identifier
        scenario_id: Scenario identifier
        discount_pct: Discount percentage (0-100)
        forecast_data: Prophet forecast DataFrame
        contract_value: Contract commitment value
        baseline_exhaustion_date: Baseline (0%) exhaustion date for comparison

    Returns:
        List of forecast records for this scenario
    """
    contract_forecast = forecast_data[forecast_data['contract_id'] == contract_id].copy()

    if contract_forecast.empty:
        return []

    discount_factor = 1 - (discount_pct / 100)
    records = []

    # Convert Decimal columns to float (required for pandas arithmetic)
    for col in ['predicted_daily_cost', 'predicted_cumulative', 'lower_bound', 'upper_bound']:
        if col in contract_forecast.columns:
            contract_forecast[col] = contract_forecast[col].astype(float)

    # Calculate scaled predictions
    contract_forecast['scaled_daily'] = contract_forecast['predicted_daily_cost'] * discount_factor
    contract_forecast['scaled_lower'] = contract_forecast['lower_bound'] * discount_factor
    contract_forecast['scaled_upper'] = contract_forecast['upper_bound'] * discount_factor

    # Recalculate cumulative
    contract_forecast['scaled_cumulative'] = contract_forecast['scaled_daily'].cumsum()
    contract_forecast['scaled_lower_cum'] = contract_forecast['scaled_lower'].cumsum()
    contract_forecast['scaled_upper_cum'] = contract_forecast['scaled_upper'].cumsum()

    # Find new exhaustion dates
    p50_mask = contract_forecast['scaled_cumulative'] >= contract_value
    p10_mask = contract_forecast['scaled_upper_cum'] >= contract_value
    p90_mask = contract_forecast['scaled_lower_cum'] >= contract_value

    scenario_ex_p50 = contract_forecast.loc[p50_mask, 'forecast_date'].min() if p50_mask.any() else None
    scenario_ex_p10 = contract_forecast.loc[p10_mask, 'forecast_date'].min() if p10_mask.any() else None
    scenario_ex_p90 = contract_forecast.loc[p90_mask, 'forecast_date'].min() if p90_mask.any() else None

    # Calculate days extended vs baseline
    days_extended = None
    if scenario_ex_p50 is not None and baseline_exhaustion_date is not None:
        scenario_ex_p50_dt = pd.to_datetime(scenario_ex_p50)
        baseline_dt = pd.to_datetime(baseline_exhaustion_date)
        days_extended = (scenario_ex_p50_dt - baseline_dt).days

    for _, row in contract_forecast.iterrows():
        # Calculate savings at baseline exhaustion
        savings_at_exhaustion = None
        if baseline_exhaustion_date is not None:
            forecast_date = pd.to_datetime(row['forecast_date'])
            baseline_dt = pd.to_datetime(baseline_exhaustion_date)
            if forecast_date <= baseline_dt:
                original_cum = float(row['predicted_cumulative']) if pd.notna(row['predicted_cumulative']) else 0
                scaled_cum = float(row['scaled_cumulative']) if pd.notna(row['scaled_cumulative']) else 0
                savings_at_exhaustion = original_cum - scaled_cum

        # Days to exhaustion for this scenario
        scenario_days_to_exhaustion = None
        if scenario_ex_p50 is not None:
            scenario_days_to_exhaustion = (pd.to_datetime(scenario_ex_p50) - pd.to_datetime(row['forecast_date'])).days
            if scenario_days_to_exhaustion < 0:
                scenario_days_to_exhaustion = 0

        records.append({
            'scenario_id': scenario_id,
            'contract_id': contract_id,
            'forecast_date': row['forecast_date'],
            'predicted_daily_cost': float(row['scaled_daily']) if pd.notna(row['scaled_daily']) else None,
            'predicted_cumulative': float(row['scaled_cumulative']) if pd.notna(row['scaled_cumulative']) else None,
            'lower_bound': float(row['scaled_lower']) if pd.notna(row['scaled_lower']) else None,
            'upper_bound': float(row['scaled_upper']) if pd.notna(row['scaled_upper']) else None,
            'exhaustion_date_p10': scenario_ex_p10,
            'exhaustion_date_p50': scenario_ex_p50,
            'exhaustion_date_p90': scenario_ex_p90,
            'days_to_exhaustion': scenario_days_to_exhaustion,
            'baseline_exhaustion_date': baseline_exhaustion_date,
            'days_extended': days_extended,
            'savings_at_exhaustion': savings_at_exhaustion,
            'model_version': row.get('model_version', 'prophet'),
            'created_at': datetime.now()
        })

    return records

# Get baseline exhaustion dates for each contract
baseline_exhaustion = {}
for _, contract in contracts_df.iterrows():
    contract_id = contract['contract_id']
    contract_forecast = forecast_df[forecast_df['contract_id'] == contract_id]
    if not contract_forecast.empty:
        ex_date = contract_forecast['exhaustion_date_p50'].iloc[0]
        # Handle NaT (Not a Time) values
        baseline_exhaustion[contract_id] = None if is_null_or_nat(ex_date) else ex_date
    else:
        baseline_exhaustion[contract_id] = None

log_debug(f"Baseline exhaustion dates: {baseline_exhaustion}")

# Calculate forecasts for all scenarios
log_debug("Calculating scenario forecasts...")
all_forecasts = []

for scenario in all_scenarios:
    contract = contracts_df[contracts_df['contract_id'] == scenario['contract_id']].iloc[0]
    forecast_records = calculate_scenario_forecast(
        scenario['contract_id'],
        scenario['scenario_id'],
        scenario['discount_pct'],
        forecast_df,
        float(contract['total_value']),
        baseline_exhaustion.get(scenario['contract_id'])
    )
    all_forecasts.extend(forecast_records)

log_debug(f"Total forecast records: {len(all_forecasts)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Summary & Sweet Spot Detection

# COMMAND ----------

def calculate_scenario_summary(scenario, burndown_records, forecast_records, contract, baseline_exhaustion_date):
    """
    Calculate summary metrics for a scenario.

    Returns:
        Summary dictionary
    """
    contract_value = float(contract['total_value'])
    discount_pct = scenario['discount_pct']

    # Get latest burndown values
    if burndown_records:
        latest_burndown = max(burndown_records, key=lambda x: x['usage_date'])
        actual_cumulative = latest_burndown['original_cumulative']
        simulated_cumulative = latest_burndown['simulated_cumulative']
        cumulative_savings = latest_burndown['cumulative_savings']
    else:
        actual_cumulative = 0
        simulated_cumulative = 0
        cumulative_savings = 0

    # Get exhaustion dates from forecasts
    scenario_exhaustion_date = None
    days_extended = None
    if forecast_records:
        scenario_exhaustion_date = forecast_records[0].get('exhaustion_date_p50')
        days_extended = forecast_records[0].get('days_extended')

    # Break-even analysis
    # break_even_consumption = commitment / (1 - discount_rate)
    discount_rate = discount_pct / 100
    if discount_rate < 1:
        break_even_consumption = contract_value / (1 - discount_rate)
    else:
        break_even_consumption = 0

    # Utilization percentage (how much of commitment is being used)
    utilization_pct = (simulated_cumulative / contract_value * 100) if contract_value > 0 else 0

    # Break-even status
    if actual_cumulative >= break_even_consumption:
        break_even_status = 'ABOVE_BREAKEVEN'
    elif actual_cumulative >= break_even_consumption * 0.8:
        break_even_status = 'AT_RISK'
    else:
        break_even_status = 'BELOW_BREAKEVEN'

    # Exhaustion status
    contract_end = pd.to_datetime(contract['end_date'])
    if scenario_exhaustion_date is not None:
        scenario_ex_dt = pd.to_datetime(scenario_exhaustion_date)
        if scenario_ex_dt < contract_end:
            exhaustion_status = 'EARLY_EXHAUSTION'
        elif scenario_ex_dt > contract_end + timedelta(days=30):
            exhaustion_status = 'EXTENDED'
        else:
            exhaustion_status = 'ON_TRACK'
    else:
        exhaustion_status = 'EXTENDED'

    # Percentage savings
    pct_savings = discount_pct  # Simplified: discount % = savings %

    # Check if this is a "what if longer duration" scenario
    is_longer_duration = scenario.get('is_longer_duration_scenario', False)
    potential_duration = scenario.get('potential_duration_years')
    current_duration = scenario.get('contract_duration_years', 1)
    is_max_for_duration = scenario.get('is_max_for_duration', False)

    return {
        'scenario_id': scenario['scenario_id'],
        'contract_id': scenario['contract_id'],
        'scenario_name': scenario['scenario_name'],
        'discount_pct': discount_pct,
        'base_commitment': contract_value,
        'scenario_commitment': contract_value,
        'contract_start': contract['start_date'],
        'contract_end': contract['end_date'],
        'actual_cumulative': actual_cumulative,
        'simulated_cumulative': simulated_cumulative,
        'cumulative_savings': cumulative_savings,
        'baseline_exhaustion_date': baseline_exhaustion_date,
        'scenario_exhaustion_date': scenario_exhaustion_date,
        'days_extended': days_extended,
        'break_even_consumption': break_even_consumption,
        'utilization_pct': utilization_pct,
        'break_even_status': break_even_status,
        'exhaustion_status': exhaustion_status,
        'pct_savings': pct_savings,
        'is_sweet_spot': False,  # Will be set later
        'is_longer_duration_scenario': is_longer_duration,
        'potential_duration_years': potential_duration,
        'contract_duration_years': current_duration,
        'is_max_for_duration': is_max_for_duration,
        'last_calculated': datetime.now()
    }

# Calculate summaries
log_debug("Calculating scenario summaries...")
all_summaries = []

for scenario in all_scenarios:
    contract = contracts_df[contracts_df['contract_id'] == scenario['contract_id']].iloc[0]

    # Get burndown and forecast records for this scenario
    scenario_burndown = [r for r in all_burndown if r['scenario_id'] == scenario['scenario_id']]
    scenario_forecast = [r for r in all_forecasts if r['scenario_id'] == scenario['scenario_id']]

    summary = calculate_scenario_summary(
        scenario,
        scenario_burndown,
        scenario_forecast,
        contract,
        baseline_exhaustion.get(scenario['contract_id'])
    )
    all_summaries.append(summary)

log_debug(f"Total summaries: {len(all_summaries)}")

# COMMAND ----------

# Sweet spot detection
# Strategy Principles:
# 1. Commit contract is a sunk cost - you pay it regardless
# 2. Any unutilized commitment at contract end is LOST money
# 3. EARLY_EXHAUSTION = missed opportunity - longer contract would give more discount
# 4. 3-year contracts are safer: more discount + less risk of overpaying
# 5. Fast consumers (30%+ in year 1) should definitely get longer contracts
log_debug("Detecting sweet spot scenarios...")

for contract_id in contracts_df['contract_id'].unique():
    contract_summaries = [s for s in all_summaries if s['contract_id'] == contract_id]
    current_scenarios = [s for s in contract_summaries if not s.get('is_longer_duration_scenario', False)]
    longer_scenarios = [s for s in contract_summaries if s.get('is_longer_duration_scenario', False)]

    # Get contract duration
    contract_duration = current_scenarios[0].get('contract_duration_years', 1) if current_scenarios else 1

    # Categorize scenarios by exhaustion status
    early_exhaust = [s for s in current_scenarios if s['exhaustion_status'] == 'EARLY_EXHAUSTION']
    on_track = [s for s in current_scenarios if s['exhaustion_status'] == 'ON_TRACK']
    extended = [s for s in current_scenarios if s['exhaustion_status'] == 'EXTENDED']

    best = None
    strategy_note = ""

    # Decision logic based on exhaustion patterns
    if on_track:
        # ON_TRACK is optimal - contract is well-sized for consumption
        best = max(on_track, key=lambda x: x['discount_pct'])
        strategy_note = "OPTIMAL - Contract well-sized, max discount with full burn"
        log_debug(f"  Contract {contract_id}: Sweet spot = {best['scenario_name']} ({best['discount_pct']}%)")
        log_debug(f"    {strategy_note}")

    elif early_exhaust:
        # EARLY_EXHAUSTION - will burn but could get better discount with longer contract
        best = max(early_exhaust, key=lambda x: x['discount_pct'])

        if contract_duration < 3:
            # Not at max duration - recommend longer contract
            strategy_note = f"SUBOPTIMAL - Exhausts early, consider longer duration for more discount"
            log_debug(f"  Contract {contract_id}: Current best = {best['scenario_name']} ({best['discount_pct']}%)")
            log_debug(f"    WARNING: {strategy_note}")
            log_debug(f"    Current duration: {contract_duration}yr - Contract will exhaust before end")

            # Show what longer duration would yield
            for ls in longer_scenarios:
                extra_discount = ls['discount_pct'] - best['discount_pct']
                potential_duration = ls.get('potential_duration_years', contract_duration + 1)
                if extra_discount > 0:
                    log_debug(f"    RECOMMEND: {potential_duration}yr contract → {ls['discount_pct']}% discount (+{extra_discount}% more)")
        else:
            # Already at 3yr max duration - this is the best we can do
            strategy_note = "GOOD - Max duration (3yr), will exhaust with best available discount"
            log_debug(f"  Contract {contract_id}: Sweet spot = {best['scenario_name']} ({best['discount_pct']}%)")
            log_debug(f"    {strategy_note}")

    elif extended:
        # EXTENDED - won't exhaust, money will be lost
        best = next((s for s in current_scenarios if s['discount_pct'] == 0), current_scenarios[0] if current_scenarios else None)
        strategy_note = "RISK - Under-consumption, commitment will not be fully utilized"
        log_debug(f"  Contract {contract_id}: WARNING - Under-consumption risk!")
        log_debug(f"    No discount scenario will exhaust contract by end date")
        log_debug(f"    Money will be LOST at contract termination")
        log_debug(f"    Consider: increase consumption OR reduce commitment amount")

        # Check if longer duration helps (more time to consume)
        longer_that_exhaust = [ls for ls in longer_scenarios if ls['exhaustion_status'] in ['EARLY_EXHAUSTION', 'ON_TRACK']]
        if longer_that_exhaust:
            best_longer = max(longer_that_exhaust, key=lambda x: x['discount_pct'])
            log_debug(f"    ALTERNATIVE: Extend to {best_longer.get('potential_duration_years')}yr to allow full consumption")

    # Mark as sweet spot
    if best:
        for summary in all_summaries:
            if summary['scenario_id'] == best['scenario_id']:
                summary['is_sweet_spot'] = True
                # Store the strategy note for dashboard display
                summary['strategy_recommendation'] = strategy_note
                break

# Also update scenarios with is_recommended flag
for scenario in all_scenarios:
    matching_summary = next((s for s in all_summaries if s['scenario_id'] == scenario['scenario_id']), None)
    if matching_summary and matching_summary.get('is_sweet_spot'):
        scenario['is_recommended'] = True

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Save Results

# COMMAND ----------

def save_scenarios(scenarios):
    """Save scenarios to discount_scenarios table."""
    if not scenarios:
        log_debug("No scenarios to save")
        return

    log_debug(f"Saving {len(scenarios)} scenarios...")

    # Clear existing scenarios
    spark.sql(f"DELETE FROM {CATALOG}.{SCHEMA}.discount_scenarios WHERE created_by = 'whatif_simulator'")

    # Insert scenarios
    for s in scenarios:
        is_baseline = 'TRUE' if s['is_baseline'] else 'FALSE'
        is_recommended = 'TRUE' if s['is_recommended'] else 'FALSE'

        # Escape single quotes in text fields
        escaped_name = s['scenario_name'].replace("'", "''") if s.get('scenario_name') else ''
        escaped_desc = s['description'].replace("'", "''") if s.get('description') else ''

        spark.sql(f"""
            INSERT INTO {CATALOG}.{SCHEMA}.discount_scenarios
            (scenario_id, contract_id, scenario_name, description, discount_pct, discount_type,
             adjusted_total_value, is_baseline, is_recommended, status, created_by, created_at)
            VALUES (
                '{s['scenario_id']}',
                '{s['contract_id']}',
                '{escaped_name}',
                '{escaped_desc}',
                {s['discount_pct']},
                '{s['discount_type']}',
                {s['adjusted_total_value']},
                {is_baseline},
                {is_recommended},
                '{s['status']}',
                '{s['created_by']}',
                CURRENT_TIMESTAMP()
            )
        """)

    log_debug(f"Saved {len(scenarios)} scenarios")

def save_burndown(burndown_records):
    """Save burndown records to scenario_burndown table."""
    if not burndown_records:
        log_debug("No burndown records to save")
        return

    log_debug(f"Saving {len(burndown_records)} burndown records...")

    # Clear existing
    spark.sql(f"DELETE FROM {CATALOG}.{SCHEMA}.scenario_burndown WHERE 1=1")

    # Insert in batches
    batch_size = 500
    for i in range(0, len(burndown_records), batch_size):
        batch = burndown_records[i:i+batch_size]
        values = []
        for r in batch:
            values.append(f"""(
                '{r['scenario_id']}',
                '{r['contract_id']}',
                '{r['usage_date']}',
                {r['original_daily_cost']},
                {r['original_cumulative']},
                {r['simulated_daily_cost']},
                {r['simulated_cumulative']},
                {r['scenario_commitment']},
                {r['simulated_remaining']},
                {r['daily_savings']},
                {r['cumulative_savings']},
                CURRENT_TIMESTAMP()
            )""")

        spark.sql(f"""
            INSERT INTO {CATALOG}.{SCHEMA}.scenario_burndown
            (scenario_id, contract_id, usage_date, original_daily_cost, original_cumulative,
             simulated_daily_cost, simulated_cumulative, scenario_commitment, simulated_remaining,
             daily_savings, cumulative_savings, calculated_at)
            VALUES {', '.join(values)}
        """)

    log_debug(f"Saved {len(burndown_records)} burndown records")

def save_forecasts(forecast_records):
    """Save forecast records to scenario_forecast table."""
    if not forecast_records:
        log_debug("No forecast records to save")
        return

    log_debug(f"Saving {len(forecast_records)} forecast records...")

    # Clear existing
    spark.sql(f"DELETE FROM {CATALOG}.{SCHEMA}.scenario_forecast WHERE 1=1")

    # Insert in batches
    batch_size = 500
    for i in range(0, len(forecast_records), batch_size):
        batch = forecast_records[i:i+batch_size]
        values = []
        for r in batch:
            # Handle nullable fields (check for None, NaN, and NaT)
            pred_daily = round(r['predicted_daily_cost'], 2) if not is_null_or_nat(r.get('predicted_daily_cost')) else 'NULL'
            pred_cum = round(r['predicted_cumulative'], 2) if not is_null_or_nat(r.get('predicted_cumulative')) else 'NULL'
            lower = round(r['lower_bound'], 2) if not is_null_or_nat(r.get('lower_bound')) else 'NULL'
            upper = round(r['upper_bound'], 2) if not is_null_or_nat(r.get('upper_bound')) else 'NULL'
            ex_p10 = safe_date_str(r.get('exhaustion_date_p10'))
            ex_p50 = safe_date_str(r.get('exhaustion_date_p50'))
            ex_p90 = safe_date_str(r.get('exhaustion_date_p90'))
            days_ex = int(r['days_to_exhaustion']) if not is_null_or_nat(r.get('days_to_exhaustion')) else 'NULL'
            baseline_ex = safe_date_str(r.get('baseline_exhaustion_date'))
            days_ext = int(r['days_extended']) if not is_null_or_nat(r.get('days_extended')) else 'NULL'
            savings_ex = round(r['savings_at_exhaustion'], 2) if not is_null_or_nat(r.get('savings_at_exhaustion')) else 'NULL'
            model_ver = r.get('model_version', 'prophet') or 'prophet'

            values.append(f"""(
                '{r['scenario_id']}',
                '{r['contract_id']}',
                '{r['forecast_date']}',
                {pred_daily},
                {pred_cum},
                {lower},
                {upper},
                {ex_p10},
                {ex_p50},
                {ex_p90},
                {days_ex},
                {baseline_ex},
                {days_ext},
                {savings_ex},
                '{model_ver}',
                CURRENT_TIMESTAMP()
            )""")

        spark.sql(f"""
            INSERT INTO {CATALOG}.{SCHEMA}.scenario_forecast
            (scenario_id, contract_id, forecast_date, predicted_daily_cost, predicted_cumulative,
             lower_bound, upper_bound, exhaustion_date_p10, exhaustion_date_p50, exhaustion_date_p90,
             days_to_exhaustion, baseline_exhaustion_date, days_extended, savings_at_exhaustion,
             model_version, created_at)
            VALUES {', '.join(values)}
        """)

    log_debug(f"Saved {len(forecast_records)} forecast records")

def save_summaries(summaries):
    """Save summary records to scenario_summary table."""
    if not summaries:
        log_debug("No summaries to save")
        return

    log_debug(f"Saving {len(summaries)} summary records...")

    # Clear existing
    spark.sql(f"DELETE FROM {CATALOG}.{SCHEMA}.scenario_summary WHERE 1=1")

    for s in summaries:
        # Handle nullable fields (check for None, NaN, and NaT)
        baseline_ex = safe_date_str(s.get('baseline_exhaustion_date'))
        scenario_ex = safe_date_str(s.get('scenario_exhaustion_date'))
        days_ext = int(s['days_extended']) if not is_null_or_nat(s.get('days_extended')) else 'NULL'
        is_sweet = 'TRUE' if s.get('is_sweet_spot') else 'FALSE'

        # Handle contract dates - use safe_date_str for proper NULL handling
        contract_start = safe_date_str(str(s['contract_start'])[:10] if not is_null_or_nat(s.get('contract_start')) else None)
        contract_end = safe_date_str(str(s['contract_end'])[:10] if not is_null_or_nat(s.get('contract_end')) else None)

        # Escape single quotes in scenario_name
        escaped_name = s['scenario_name'].replace("'", "''") if s.get('scenario_name') else ''

        spark.sql(f"""
            INSERT INTO {CATALOG}.{SCHEMA}.scenario_summary
            (scenario_id, contract_id, scenario_name, discount_pct, base_commitment, scenario_commitment,
             contract_start, contract_end, actual_cumulative, simulated_cumulative, cumulative_savings,
             baseline_exhaustion_date, scenario_exhaustion_date, days_extended, break_even_consumption,
             utilization_pct, break_even_status, exhaustion_status, pct_savings, is_sweet_spot, last_calculated)
            VALUES (
                '{s['scenario_id']}',
                '{s['contract_id']}',
                '{escaped_name}',
                {s['discount_pct']},
                {s['base_commitment']},
                {s['scenario_commitment']},
                {contract_start},
                {contract_end},
                {round(s['actual_cumulative'], 2)},
                {round(s['simulated_cumulative'], 2)},
                {round(s['cumulative_savings'], 2)},
                {baseline_ex},
                {scenario_ex},
                {days_ext},
                {round(s['break_even_consumption'], 2)},
                {round(s['utilization_pct'], 2)},
                '{s['break_even_status']}',
                '{s['exhaustion_status']}',
                {round(s['pct_savings'], 2)},
                {is_sweet},
                CURRENT_TIMESTAMP()
            )
        """)

    log_debug(f"Saved {len(summaries)} summary records")

# COMMAND ----------

# Save all results
log_debug("="*60)
log_debug("SAVING RESULTS")
log_debug("="*60)

try:
    save_scenarios(all_scenarios)
except Exception as e:
    log_debug(f"ERROR in save_scenarios: {str(e)}")
    log_debug(f"Stack trace: {traceback.format_exc()}")
    save_debug_log()
    raise

try:
    save_burndown(all_burndown)
except Exception as e:
    log_debug(f"ERROR in save_burndown: {str(e)}")
    log_debug(f"Stack trace: {traceback.format_exc()}")
    save_debug_log()
    raise

try:
    save_forecasts(all_forecasts)
except Exception as e:
    log_debug(f"ERROR in save_forecasts: {str(e)}")
    log_debug(f"Stack trace: {traceback.format_exc()}")
    save_debug_log()
    raise

try:
    save_summaries(all_summaries)
except Exception as e:
    log_debug(f"ERROR in save_summaries: {str(e)}")
    log_debug(f"Stack trace: {traceback.format_exc()}")
    save_debug_log()
    raise

log_debug("="*60)
log_debug("WHAT-IF SIMULATION COMPLETE")
log_debug("="*60)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Validation & Summary

# COMMAND ----------

# Display scenario summary by contract
print("Scenario Summary (Current Duration Scenarios):")
display(spark.sql(f"""
SELECT
  ss.contract_id,
  ss.scenario_name,
  ss.discount_pct,
  ROUND(ss.cumulative_savings, 2) as savings_to_date,
  ss.scenario_exhaustion_date,
  ss.days_extended,
  ROUND(ss.utilization_pct, 1) as utilization_pct,
  ss.exhaustion_status,
  CASE WHEN ss.is_sweet_spot THEN 'RECOMMENDED' ELSE '' END as status
FROM {CATALOG}.{SCHEMA}.scenario_summary ss
JOIN {CATALOG}.{SCHEMA}.discount_scenarios ds ON ss.scenario_id = ds.scenario_id
WHERE COALESCE(ds.description, '') NOT LIKE '%extended to%'
ORDER BY ss.contract_id, ss.discount_pct
"""))

# COMMAND ----------

# Display "What If Longer Duration" opportunities
print("\nLonger Duration Opportunities (Incentive to Extend):")
display(spark.sql(f"""
SELECT
  ss.contract_id,
  ss.scenario_name,
  ss.discount_pct as potential_discount,
  ROUND(ss.cumulative_savings, 2) as potential_savings,
  ss.days_extended as potential_days_extended,
  ds.description as opportunity
FROM {CATALOG}.{SCHEMA}.scenario_summary ss
JOIN {CATALOG}.{SCHEMA}.discount_scenarios ds ON ss.scenario_id = ds.scenario_id
WHERE ds.description LIKE '%extended to%'
ORDER BY ss.contract_id, ss.discount_pct
"""))

# COMMAND ----------

# Display sweet spot recommendations with comparison
print("\nSweet Spot Recommendations (Best Achievable with Current Duration):")
display(spark.sql(f"""
SELECT
  contract_id,
  scenario_name,
  discount_pct as best_discount,
  ROUND(cumulative_savings, 2) as savings,
  days_extended,
  ROUND(utilization_pct, 1) as utilization_pct
FROM {CATALOG}.{SCHEMA}.scenario_summary
WHERE is_sweet_spot = TRUE
"""))

# COMMAND ----------

# Show discount tiers for reference
print("\nDiscount Tier Reference (Longer Duration = Higher Max Discount):")
display(spark.sql(f"""
SELECT
  tier_name,
  CONCAT('$', FORMAT_NUMBER(min_commitment, 0), ' - ',
         COALESCE(CONCAT('$', FORMAT_NUMBER(max_commitment, 0)), 'Unlimited')) as commitment_range,
  duration_years as years,
  CONCAT(CAST(discount_rate * 100 AS INT), '%') as max_discount
FROM {CATALOG}.{SCHEMA}.discount_tiers
ORDER BY min_commitment, duration_years
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Notebook Exit

# COMMAND ----------

result = {
    "contracts_processed": len(contracts_df),
    "scenarios_generated": len(all_scenarios),
    "burndown_records": len(all_burndown),
    "forecast_records": len(all_forecasts),
    "status": "SUCCESS"
}

log_debug(f"Result: {result}")
log_debug("=== WHAT-IF SIMULATOR COMPLETED SUCCESSFULLY ===")
save_debug_log()

print(f"\nResult: {result}")
dbutils.notebook.exit(str(result))
