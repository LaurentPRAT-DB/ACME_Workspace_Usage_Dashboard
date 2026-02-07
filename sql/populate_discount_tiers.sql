-- Populate Discount Tiers with Default Values
-- Based on typical cloud commit discount structures
-- These values are illustrative and should be adjusted for actual negotiations

-- Clear existing tiers (for fresh install)
DELETE FROM main.account_monitoring_dev.discount_tiers WHERE tier_id IS NOT NULL;

-- ============================================================================
-- Insert Default Discount Tiers
-- Structure: Commitment Level x Duration = Discount Rate
-- ============================================================================

INSERT INTO main.account_monitoring_dev.discount_tiers
  (tier_id, tier_name, min_commitment, max_commitment, duration_years, discount_rate, notes, effective_date)
VALUES
  -- Entry Tier: $50K - $100K
  ('TIER_50K_1Y', 'Entry - 1 Year', 50000, 99999, 1, 0.05, 'Entry level commit, 1 year term', '2024-01-01'),
  ('TIER_50K_2Y', 'Entry - 2 Year', 50000, 99999, 2, 0.08, 'Entry level commit, 2 year term', '2024-01-01'),
  ('TIER_50K_3Y', 'Entry - 3 Year', 50000, 99999, 3, 0.10, 'Entry level commit, 3 year term', '2024-01-01'),

  -- Standard Tier: $100K - $250K
  ('TIER_100K_1Y', 'Standard - 1 Year', 100000, 249999, 1, 0.10, 'Standard commit, 1 year term', '2024-01-01'),
  ('TIER_100K_2Y', 'Standard - 2 Year', 100000, 249999, 2, 0.15, 'Standard commit, 2 year term', '2024-01-01'),
  ('TIER_100K_3Y', 'Standard - 3 Year', 100000, 249999, 3, 0.18, 'Standard commit, 3 year term', '2024-01-01'),

  -- Growth Tier: $250K - $500K
  ('TIER_250K_1Y', 'Growth - 1 Year', 250000, 499999, 1, 0.15, 'Growth commit, 1 year term', '2024-01-01'),
  ('TIER_250K_2Y', 'Growth - 2 Year', 250000, 499999, 2, 0.20, 'Growth commit, 2 year term', '2024-01-01'),
  ('TIER_250K_3Y', 'Growth - 3 Year', 250000, 499999, 3, 0.25, 'Growth commit, 3 year term', '2024-01-01'),

  -- Scale Tier: $500K - $1M
  ('TIER_500K_1Y', 'Scale - 1 Year', 500000, 999999, 1, 0.20, 'Scale commit, 1 year term', '2024-01-01'),
  ('TIER_500K_2Y', 'Scale - 2 Year', 500000, 999999, 2, 0.25, 'Scale commit, 2 year term', '2024-01-01'),
  ('TIER_500K_3Y', 'Scale - 3 Year', 500000, 999999, 3, 0.30, 'Scale commit, 3 year term', '2024-01-01'),

  -- Enterprise Tier: $1M - $5M
  ('TIER_1M_1Y', 'Enterprise - 1 Year', 1000000, 4999999, 1, 0.25, 'Enterprise commit, 1 year term', '2024-01-01'),
  ('TIER_1M_2Y', 'Enterprise - 2 Year', 1000000, 4999999, 2, 0.30, 'Enterprise commit, 2 year term', '2024-01-01'),
  ('TIER_1M_3Y', 'Enterprise - 3 Year', 1000000, 4999999, 3, 0.35, 'Enterprise commit, 3 year term', '2024-01-01'),

  -- Strategic Tier: $5M+
  ('TIER_5M_1Y', 'Strategic - 1 Year', 5000000, NULL, 1, 0.30, 'Strategic commit, 1 year term', '2024-01-01'),
  ('TIER_5M_2Y', 'Strategic - 2 Year', 5000000, NULL, 2, 0.35, 'Strategic commit, 2 year term', '2024-01-01'),
  ('TIER_5M_3Y', 'Strategic - 3 Year', 5000000, NULL, 3, 0.40, 'Strategic commit, 3 year term', '2024-01-01');

-- ============================================================================
-- Create default scenarios for each contract
-- These are the pre-computed discount levels: 0%, 5%, 10%, 15%, 20%
-- ============================================================================

-- Function to create default scenarios will be in the simulator notebook
-- This SQL just sets up the tier configuration

-- ============================================================================
-- Verification Query
-- ============================================================================
SELECT
  tier_name,
  CONCAT('$', FORMAT_NUMBER(min_commitment, 0), ' - ',
         COALESCE(CONCAT('$', FORMAT_NUMBER(max_commitment, 0)), 'Unlimited')) as commitment_range,
  duration_years as years,
  CONCAT(CAST(discount_rate * 100 AS INT), '%') as discount
FROM main.account_monitoring_dev.discount_tiers
ORDER BY min_commitment, duration_years;

SELECT CONCAT('Populated ', COUNT(*), ' discount tiers') as status
FROM main.account_monitoring_dev.discount_tiers;
