#!/bin/bash
# Deploy Contract Consumption Monitor Lakeview Dashboard
# Usage: ./scripts/deploy_dashboard.sh [profile]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DASHBOARD_JSON="$PROJECT_DIR/resources/dashboards/contract_consumption_monitor.json"

# Default profile
PROFILE="${1:-LPT_FREE_EDITION}"

echo "=============================================="
echo "Contract Consumption Monitor Dashboard Deploy"
echo "=============================================="
echo "Profile: $PROFILE"
echo ""

# Check if Databricks CLI is installed
if ! command -v databricks &> /dev/null; then
    echo "Error: Databricks CLI is not installed"
    echo "Install with: pip install databricks-cli"
    exit 1
fi

# Get current user email
echo "Getting current user..."
USER_EMAIL=$(databricks auth describe --profile "$PROFILE" 2>/dev/null | grep -i "User:" | awk '{print $2}')
if [ -z "$USER_EMAIL" ]; then
    # Alternative method
    USER_EMAIL=$(databricks current-user me --profile "$PROFILE" 2>/dev/null | jq -r '.userName' 2>/dev/null)
fi

if [ -z "$USER_EMAIL" ]; then
    echo "Error: Could not determine current user. Please check your authentication."
    echo "Run: databricks auth login --profile $PROFILE"
    exit 1
fi

echo "User: $USER_EMAIL"

# Get warehouse ID from databricks.yml
WAREHOUSE_ID=$(grep -A1 "warehouse_id:" "$PROJECT_DIR/databricks.yml" | tail -1 | grep -oE '"[^"]+"' | tr -d '"')
if [ -z "$WAREHOUSE_ID" ]; then
    WAREHOUSE_ID="58d41113cb262dce"  # Default from databricks.yml
fi
echo "Warehouse ID: $WAREHOUSE_ID"

# Read and escape the dashboard JSON
echo ""
echo "Reading dashboard configuration..."
SERIALIZED_DASHBOARD=$(cat "$DASHBOARD_JSON" | jq -c .)

# Check if dashboard already exists
echo "Checking for existing dashboard..."
EXISTING_DASHBOARD=$(databricks api get /api/2.0/lakeview/dashboards --profile "$PROFILE" 2>/dev/null | \
    jq -r '.dashboards[] | select(.display_name == "Contract Consumption Monitor") | .dashboard_id' 2>/dev/null | head -1)

if [ -n "$EXISTING_DASHBOARD" ] && [ "$EXISTING_DASHBOARD" != "null" ]; then
    echo "Found existing dashboard: $EXISTING_DASHBOARD"
    echo "Updating dashboard..."

    # Update existing dashboard
    databricks api patch "/api/2.0/lakeview/dashboards/$EXISTING_DASHBOARD" --profile "$PROFILE" --json "{
        \"display_name\": \"Contract Consumption Monitor\",
        \"serialized_dashboard\": $(echo "$SERIALIZED_DASHBOARD" | jq -Rs .)
    }"

    DASHBOARD_ID="$EXISTING_DASHBOARD"
    echo "Dashboard updated successfully!"
else
    echo "Creating new dashboard..."

    # Create new dashboard
    RESPONSE=$(databricks api post /api/2.0/lakeview/dashboards --profile "$PROFILE" --json "{
        \"display_name\": \"Contract Consumption Monitor\",
        \"warehouse_id\": \"$WAREHOUSE_ID\",
        \"parent_path\": \"/Users/$USER_EMAIL\",
        \"serialized_dashboard\": $(echo "$SERIALIZED_DASHBOARD" | jq -Rs .)
    }")

    DASHBOARD_ID=$(echo "$RESPONSE" | jq -r '.dashboard_id')

    if [ -z "$DASHBOARD_ID" ] || [ "$DASHBOARD_ID" == "null" ]; then
        echo "Error creating dashboard:"
        echo "$RESPONSE"
        exit 1
    fi

    echo "Dashboard created successfully!"
fi

echo ""
echo "=============================================="
echo "Dashboard ID: $DASHBOARD_ID"
echo ""

# Publish the dashboard
echo "Publishing dashboard..."
databricks api post "/api/2.0/lakeview/dashboards/$DASHBOARD_ID/published" --profile "$PROFILE" --json '{"embed_credentials": true}' 2>/dev/null || true

# Get workspace URL
WORKSPACE_URL=$(databricks auth describe --profile "$PROFILE" 2>/dev/null | grep -i "^Host:" | awk '{print $2}' | sed 's/\/$//' | head -1)
if [ -z "$WORKSPACE_URL" ]; then
    WORKSPACE_URL=$(databricks auth env --profile "$PROFILE" 2>/dev/null | grep DATABRICKS_HOST | cut -d'=' -f2)
fi

echo ""
echo "=============================================="
echo "Dashboard deployed successfully!"
echo "=============================================="
echo ""
echo "View your dashboard at:"
echo "${WORKSPACE_URL}/sql/dashboardsv3/${DASHBOARD_ID}"
echo ""
