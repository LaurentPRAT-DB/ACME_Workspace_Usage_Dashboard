#!/bin/bash
# ============================================================================
# Account Monitor - First Install Script
# ============================================================================
# This script performs a complete first-time installation:
# 1. Validates prerequisites
# 2. Deploys the Databricks Asset Bundle
# 3. Runs the first install job (creates tables, loads data, trains model)
# 4. Provides next steps
#
# Usage:
#   ./scripts/first_install.sh --profile YOUR_PROFILE
#
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print banner
echo ""
echo "============================================================"
echo "  Databricks Account Monitor - First Install"
echo "============================================================"
echo ""

# Parse arguments
PROFILE=""
SKIP_DEPLOY=false
WAIT_FOR_COMPLETION=true

while [[ $# -gt 0 ]]; do
  case $1 in
    --profile|-p)
      PROFILE="$2"
      shift 2
      ;;
    --skip-deploy)
      SKIP_DEPLOY=true
      shift
      ;;
    --no-wait)
      WAIT_FOR_COMPLETION=false
      shift
      ;;
    --help|-h)
      echo "Usage: $0 --profile PROFILE_NAME [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --profile, -p    Databricks CLI profile name (required)"
      echo "  --skip-deploy    Skip bundle deployment (use if already deployed)"
      echo "  --no-wait        Don't wait for job completion"
      echo "  --help, -h       Show this help message"
      echo ""
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      exit 1
      ;;
  esac
done

# Validate profile
if [ -z "$PROFILE" ]; then
  echo -e "${RED}Error: --profile is required${NC}"
  echo ""
  echo "Usage: $0 --profile YOUR_PROFILE"
  echo ""
  echo "Available profiles:"
  databricks auth profiles 2>/dev/null || echo "  (run 'databricks auth login' to create a profile)"
  exit 1
fi

# Check prerequisites
echo -e "${BLUE}[1/5] Checking prerequisites...${NC}"

# Check databricks CLI
if ! command -v databricks &> /dev/null; then
  echo -e "${RED}Error: Databricks CLI not found${NC}"
  echo "Install with: pip install databricks-cli"
  exit 1
fi
echo "  ✓ Databricks CLI installed"

# Check profile exists
if ! databricks auth env --profile "$PROFILE" &> /dev/null; then
  echo -e "${RED}Error: Profile '$PROFILE' not found or not authenticated${NC}"
  echo "Run: databricks auth login --host YOUR_WORKSPACE_URL --profile $PROFILE"
  exit 1
fi
echo "  ✓ Profile '$PROFILE' authenticated"

# Check contracts.yml exists
if [ ! -f "config/contracts.yml" ]; then
  echo -e "${RED}Error: config/contracts.yml not found${NC}"
  echo "Please create your contract configuration first"
  exit 1
fi
echo "  ✓ config/contracts.yml found"

# Validate bundle
echo ""
echo -e "${BLUE}[2/5] Validating bundle configuration...${NC}"
if ! databricks bundle validate --profile "$PROFILE" 2>&1; then
  echo -e "${RED}Error: Bundle validation failed${NC}"
  exit 1
fi
echo "  ✓ Bundle configuration valid"

# Deploy bundle
if [ "$SKIP_DEPLOY" = false ]; then
  echo ""
  echo -e "${BLUE}[3/5] Deploying bundle to Databricks...${NC}"
  databricks bundle deploy --profile "$PROFILE"
  echo "  ✓ Bundle deployed successfully"
else
  echo ""
  echo -e "${YELLOW}[3/5] Skipping deployment (--skip-deploy)${NC}"
fi

# Run first install job
echo ""
echo -e "${BLUE}[4/5] Running first install job...${NC}"
echo "  This will:"
echo "    - Create Unity Catalog schema and tables"
echo "    - Load contracts from config/contracts.yml"
echo "    - Populate data from system.billing.usage"
echo "    - Train Prophet ML model"
echo "    - Generate consumption forecasts"
echo ""

RUN_OUTPUT=$(databricks bundle run account_monitor_first_install --profile "$PROFILE" 2>&1)
RUN_ID=$(echo "$RUN_OUTPUT" | grep -oE 'Run ID: [0-9]+' | grep -oE '[0-9]+' || echo "$RUN_OUTPUT" | grep -oE '[0-9]+' | head -1)

if [ -z "$RUN_ID" ]; then
  echo -e "${YELLOW}Job started. Check Databricks UI for status.${NC}"
  echo "$RUN_OUTPUT"
else
  echo "  Job started with Run ID: $RUN_ID"

  if [ "$WAIT_FOR_COMPLETION" = true ]; then
    echo ""
    echo "  Waiting for job completion (this may take several minutes)..."
    echo "  You can also monitor progress in the Databricks Jobs UI"
    echo ""

    # Poll for completion
    while true; do
      STATUS=$(databricks runs get --run-id "$RUN_ID" --profile "$PROFILE" 2>/dev/null | grep -oE '"state":\s*\{[^}]+\}' | grep -oE '"life_cycle_state":\s*"[^"]+"' | grep -oE '"[A-Z_]+"$' | tr -d '"' || echo "UNKNOWN")

      case $STATUS in
        TERMINATED)
          RESULT=$(databricks runs get --run-id "$RUN_ID" --profile "$PROFILE" 2>/dev/null | grep -oE '"result_state":\s*"[^"]+"' | grep -oE '"[A-Z]+"$' | tr -d '"' || echo "UNKNOWN")
          if [ "$RESULT" = "SUCCESS" ]; then
            echo -e "  ${GREEN}✓ Job completed successfully!${NC}"
          else
            echo -e "  ${RED}✗ Job completed with status: $RESULT${NC}"
            echo "  Check the Databricks Jobs UI for details"
            exit 1
          fi
          break
          ;;
        INTERNAL_ERROR|SKIPPED|CANCELED)
          echo -e "  ${RED}✗ Job failed with status: $STATUS${NC}"
          exit 1
          ;;
        PENDING|RUNNING|TERMINATING)
          echo -n "."
          sleep 10
          ;;
        *)
          echo -n "."
          sleep 10
          ;;
      esac
    done
  fi
fi

# Success message
echo ""
echo -e "${BLUE}[5/5] Installation complete!${NC}"
echo ""
echo "============================================================"
echo -e "${GREEN}SUCCESS: Account Monitor is ready to use${NC}"
echo "============================================================"
echo ""
echo "Next steps:"
echo ""
echo "  1. Open your Databricks workspace"
echo "  2. Navigate to: Workspace > Users > your-email > account_monitor > files > notebooks"
echo "  3. Open 'account_monitor_notebook'"
echo "  4. Click 'Run All' to see the dashboard"
echo ""
echo "Scheduled jobs (now active):"
echo "  - Daily Refresh:    2:00 AM UTC"
echo "  - Weekly Training:  Sunday 3:00 AM UTC"
echo "  - Weekly Review:    Monday 8:00 AM UTC"
echo "  - Monthly Summary:  1st of month 6:00 AM UTC"
echo ""
echo "============================================================"
