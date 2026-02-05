#!/bin/bash
# Notebook Fix Helper Script
# Automates versioning and git operations for notebook fixes
# Usage: ./scripts/notebook_fix.sh <notebook_file> "<commit_message>"

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check arguments
if [ $# -lt 2 ]; then
    echo -e "${RED}Usage: $0 <notebook_file> \"<commit_message>\"${NC}"
    echo ""
    echo "Example:"
    echo "  $0 notebooks/account_monitor_notebook.py \"Fix SQL parameter issue\""
    exit 1
fi

NOTEBOOK_FILE="$1"
COMMIT_MSG="$2"

# Verify file exists
if [ ! -f "$NOTEBOOK_FILE" ]; then
    echo -e "${RED}Error: File not found: $NOTEBOOK_FILE${NC}"
    exit 1
fi

echo -e "${BLUE}=== Notebook Fix Helper ===${NC}"
echo ""

# Extract current version
CURRENT_VERSION=$(grep -m 1 "VERSION = " "$NOTEBOOK_FILE" | sed 's/VERSION = "\(.*\)"/\1/')
CURRENT_BUILD=$(grep -m 1 "BUILD = " "$NOTEBOOK_FILE" | sed 's/BUILD = "\(.*\)"/\1/')

if [ -z "$CURRENT_VERSION" ]; then
    echo -e "${RED}Error: Could not find VERSION in $NOTEBOOK_FILE${NC}"
    exit 1
fi

echo -e "Current version: ${YELLOW}$CURRENT_VERSION${NC} (Build: $CURRENT_BUILD)"

# Calculate next version
IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
MAJOR="${VERSION_PARTS[0]}"
MINOR="${VERSION_PARTS[1]}"
PATCH="${VERSION_PARTS[2]}"

# Increment patch version
NEW_PATCH=$((PATCH + 1))
NEW_VERSION="$MAJOR.$MINOR.$NEW_PATCH"

# Calculate new build
CURRENT_DATE=$(date +%Y-%m-%d)
BUILD_DATE=$(echo "$CURRENT_BUILD" | cut -d'-' -f1-3)

if [ "$BUILD_DATE" = "$CURRENT_DATE" ]; then
    # Same day, increment build number
    BUILD_NUM=$(echo "$CURRENT_BUILD" | cut -d'-' -f4)
    NEW_BUILD_NUM=$(printf "%03d" $((10#$BUILD_NUM + 1)))
    NEW_BUILD="$CURRENT_DATE-$NEW_BUILD_NUM"
else
    # New day, reset to 001
    NEW_BUILD="$CURRENT_DATE-001"
fi

echo -e "New version:     ${GREEN}$NEW_VERSION${NC} (Build: $NEW_BUILD)"
echo ""

# Ask for confirmation
read -p "Update version and commit? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Aborted.${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}Step 1: Updating version numbers...${NC}"

# Update VERSION constant
sed -i.bak "s/VERSION = \"$CURRENT_VERSION\"/VERSION = \"$NEW_VERSION\"/" "$NOTEBOOK_FILE"

# Update BUILD constant
sed -i.bak "s/BUILD = \"$CURRENT_BUILD\"/BUILD = \"$NEW_BUILD\"/" "$NOTEBOOK_FILE"

# Update markdown header version
CURRENT_HEADER_VERSION=$(grep -m 1 "# MAGIC.*Version:" "$NOTEBOOK_FILE" | sed 's/.*Version:\*\* \([^ ]*\).*/\1/' || echo "")
if [ -n "$CURRENT_HEADER_VERSION" ]; then
    sed -i.bak "s/Version:\*\* $CURRENT_HEADER_VERSION (Build: $CURRENT_BUILD)/Version:** $NEW_VERSION (Build: $NEW_BUILD)/" "$NOTEBOOK_FILE"
fi

# Remove backup file
rm -f "$NOTEBOOK_FILE.bak"

echo -e "${GREEN}✓ Version updated${NC}"
echo ""

# Git operations
echo -e "${BLUE}Step 2: Git operations...${NC}"

# Stage the file
git add "$NOTEBOOK_FILE"
echo -e "${GREEN}✓ File staged${NC}"

# Create commit message
FULL_COMMIT_MSG="$COMMIT_MSG

- Version bumped to $NEW_VERSION (Build: $NEW_BUILD)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Commit
git commit -m "$FULL_COMMIT_MSG"
echo -e "${GREEN}✓ Changes committed${NC}"

# Push
echo ""
echo -e "${BLUE}Step 3: Pushing to remote...${NC}"
git push
echo -e "${GREEN}✓ Pushed to remote${NC}"

# Deploy
echo ""
echo -e "${BLUE}Step 4: Deploying to Databricks...${NC}"
databricks bundle deploy
echo -e "${GREEN}✓ Deployed to workspace${NC}"

# Summary
echo ""
echo -e "${GREEN}=== Success! ===${NC}"
echo ""
echo "Summary:"
echo "  File: $NOTEBOOK_FILE"
echo "  Version: $CURRENT_VERSION → $NEW_VERSION"
echo "  Build: $CURRENT_BUILD → $NEW_BUILD"
echo "  Commit: $(git log -1 --pretty=format:'%h - %s')"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Test the notebook in Databricks workspace"
echo "  2. Verify version number displays correctly"
echo "  3. Confirm the fix resolves the issue"
echo ""
