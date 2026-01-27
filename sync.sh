#!/bin/bash
# Quick Sync Script for Account Monitor
# Syncs local files to Databricks workspace using databricks CLI

set -e

# Configuration
PROFILE="${DATABRICKS_PROFILE:-LPT_FREE_EDITION}"
TARGET="${TARGET:-dev}"
COLOR_GREEN='\033[0;32m'
COLOR_RED='\033[0;31m'
COLOR_BLUE='\033[0;34m'
COLOR_YELLOW='\033[1;33m'
COLOR_RESET='\033[0m'

# Get current user
USER_EMAIL=$(databricks current-user me --profile "$PROFILE" --output json 2>/dev/null | jq -r '.userName')
BASE_PATH="/Workspace/Users/${USER_EMAIL}/account_monitor"

echo -e "${COLOR_BLUE}======================================================================${COLOR_RESET}"
echo -e "${COLOR_BLUE}🚀 Account Monitor - Quick Sync${COLOR_RESET}"
echo -e "${COLOR_BLUE}======================================================================${COLOR_RESET}"
echo -e "Profile: ${COLOR_GREEN}${PROFILE}${COLOR_RESET}"
echo -e "User: ${COLOR_GREEN}${USER_EMAIL}${COLOR_RESET}"
echo -e "Target: ${COLOR_GREEN}${BASE_PATH}${COLOR_RESET}"
echo -e "${COLOR_BLUE}======================================================================${COLOR_RESET}\n"

# Function to upload file
upload_file() {
    local local_path="$1"
    local remote_path="$2"
    local format="$3"

    if [ ! -f "$local_path" ]; then
        echo -e "  ${COLOR_YELLOW}⚠️  Skipped (not found): ${local_path}${COLOR_RESET}"
        return
    fi

    if databricks workspace import "$remote_path" \
        --file "$local_path" --language PYTHON --format "$format" --overwrite \
        --profile "$PROFILE" &>/dev/null; then
        echo -e "  ${COLOR_GREEN}✅ ${local_path}${COLOR_RESET}"
    else
        echo -e "  ${COLOR_RED}❌ Failed: ${local_path}${COLOR_RESET}"
    fi
}

# Function to upload SQL file
upload_sql() {
    local local_path="$1"
    local remote_path="$2"

    if [ ! -f "$local_path" ]; then
        echo -e "  ${COLOR_YELLOW}⚠️  Skipped (not found): ${local_path}${COLOR_RESET}"
        return
    fi

    if databricks workspace import "$remote_path" \
        --file "$local_path" --language SQL --format SOURCE --overwrite \
        --profile "$PROFILE" &>/dev/null; then
        echo -e "  ${COLOR_GREEN}✅ ${local_path}${COLOR_RESET}"
    else
        echo -e "  ${COLOR_RED}❌ Failed: ${local_path}${COLOR_RESET}"
    fi
}

# Function to create directory
create_dir() {
    databricks workspace mkdirs "$1" --profile "$PROFILE" &>/dev/null || true
}

# Create base directories
echo -e "${COLOR_BLUE}📁 Creating directories...${COLOR_RESET}"
create_dir "$BASE_PATH"
create_dir "$BASE_PATH/notebooks"
create_dir "$BASE_PATH/sql"
create_dir "$BASE_PATH/docs"
create_dir "$BASE_PATH/queries"
echo -e "  ${COLOR_GREEN}✅ Directories created${COLOR_RESET}\n"

# Sync notebooks
echo -e "${COLOR_BLUE}📓 Syncing notebooks...${COLOR_RESET}"
upload_file "post_deployment_validation.py" "$BASE_PATH/notebooks/post_deployment_validation" "SOURCE"
upload_file "account_monitor_notebook.py" "$BASE_PATH/notebooks/account_monitor_notebook" "SOURCE"
upload_sql "verify_contract_burndown.sql" "$BASE_PATH/notebooks/verify_contract_burndown"
upload_sql "lakeview_dashboard_queries.sql" "$BASE_PATH/notebooks/lakeview_dashboard_queries"
echo ""

# Sync SQL files
echo -e "${COLOR_BLUE}📊 Syncing SQL files...${COLOR_RESET}"
for sql_file in sql/*.sql; do
    if [ -f "$sql_file" ]; then
        filename=$(basename "$sql_file" .sql)
        upload_sql "$sql_file" "$BASE_PATH/sql/$filename"
    fi
done
echo ""

# Sync queries
echo -e "${COLOR_BLUE}🔍 Syncing queries...${COLOR_RESET}"
upload_sql "account_monitor_queries_CORRECTED.sql" "$BASE_PATH/queries/account_monitor_queries_CORRECTED"
echo ""

# Sync documentation
echo -e "${COLOR_BLUE}📚 Syncing documentation...${COLOR_RESET}"
for doc in README.md START_HERE.md SCHEMA_REFERENCE.md QUICK_REFERENCE.md \
           OPERATIONS_GUIDE.md POST_DEPLOYMENT_VALIDATION.md DAB_README.md \
           CONTRACT_BURNDOWN_GUIDE.md BURNDOWN_IMPLEMENTATION_SUMMARY.md \
           CREATE_LAKEVIEW_DASHBOARD.md; do
    if [ -f "$doc" ]; then
        filename=$(basename "$doc" .md)
        if databricks workspace import "$BASE_PATH/docs/$filename" \
            --file "$doc" --format AUTO --overwrite --profile "$PROFILE" &>/dev/null; then
            echo -e "  ${COLOR_GREEN}✅ ${doc}${COLOR_RESET}"
        else
            echo -e "  ${COLOR_RED}❌ Failed: ${doc}${COLOR_RESET}"
        fi
    fi
done
echo ""

# Summary
echo -e "${COLOR_BLUE}======================================================================${COLOR_RESET}"
echo -e "${COLOR_GREEN}🎉 Sync completed!${COLOR_RESET}"
echo -e "${COLOR_BLUE}======================================================================${COLOR_RESET}"
echo -e "\n📍 View in workspace:"
echo -e "   ${COLOR_BLUE}${BASE_PATH}${COLOR_RESET}"
echo -e "\n📝 Next steps:"
echo -e "   1. Open ${COLOR_GREEN}notebooks/post_deployment_validation${COLOR_RESET}"
echo -e "   2. Click ${COLOR_GREEN}'Run All'${COLOR_RESET} to validate deployment"
echo -e "   3. Check ${COLOR_GREEN}docs/${COLOR_RESET} for documentation"
echo ""
