#!/usr/bin/env python3
"""
Sync Local Repository to Databricks Workspace
Uploads notebooks, SQL files, and documentation to your workspace
"""

import sys
import os
from pathlib import Path
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.workspace import ImportFormat, Language
import argparse

# Configuration
PROFILE = "LPT_FREE_EDITION"
BASE_PATH = "/Workspace/Users/{user}/account_monitor"

# Files to sync
FILES_TO_SYNC = {
    # Notebooks
    "notebooks": {
        "post_deployment_validation.py": {
            "format": ImportFormat.SOURCE,
            "language": Language.PYTHON
        },
        "account_monitor_notebook.py": {
            "format": ImportFormat.SOURCE,
            "language": Language.PYTHON
        }
    },
    # SQL Files
    "sql": {
        "setup_schema.sql": {"format": ImportFormat.SOURCE, "language": Language.SQL},
        "refresh_dashboard_data.sql": {"format": ImportFormat.SOURCE, "language": Language.SQL},
        "check_data_freshness.sql": {"format": ImportFormat.SOURCE, "language": Language.SQL},
        "contract_analysis.sql": {"format": ImportFormat.SOURCE, "language": Language.SQL},
        "cost_anomalies.sql": {"format": ImportFormat.SOURCE, "language": Language.SQL},
        "top_consumers.sql": {"format": ImportFormat.SOURCE, "language": Language.SQL},
        "monthly_summary.sql": {"format": ImportFormat.SOURCE, "language": Language.SQL},
        "archive_old_data.sql": {"format": ImportFormat.SOURCE, "language": Language.SQL},
        "optimize_tables.sql": {"format": ImportFormat.SOURCE, "language": Language.SQL},
        "insert_sample_data.sql": {"format": ImportFormat.SOURCE, "language": Language.SQL}
    },
    # Documentation
    "docs": {
        "README.md": {"format": ImportFormat.SOURCE, "language": None},
        "START_HERE.md": {"format": ImportFormat.SOURCE, "language": None},
        "SCHEMA_REFERENCE.md": {"format": ImportFormat.SOURCE, "language": None},
        "QUICK_REFERENCE.md": {"format": ImportFormat.SOURCE, "language": None},
        "OPERATIONS_GUIDE.md": {"format": ImportFormat.SOURCE, "language": None},
        "POST_DEPLOYMENT_VALIDATION.md": {"format": ImportFormat.SOURCE, "language": None},
        "DAB_README.md": {"format": ImportFormat.SOURCE, "language": None}
    },
    # SQL Queries
    "queries": {
        "account_monitor_queries_CORRECTED.sql": {
            "format": ImportFormat.SOURCE,
            "language": Language.SQL
        }
    }
}


class WorkspaceSync:
    def __init__(self, profile: str = PROFILE, dry_run: bool = False):
        """Initialize workspace sync"""
        self.profile = profile
        self.dry_run = dry_run
        self.w = WorkspaceClient(profile=profile)
        self.current_user = self.w.current_user.me()
        self.base_path = BASE_PATH.format(user=self.current_user.user_name)
        self.stats = {"uploaded": 0, "failed": 0, "skipped": 0}

    def create_directory(self, path: str):
        """Create directory if it doesn't exist"""
        try:
            if not self.dry_run:
                self.w.workspace.mkdirs(path)
            print(f"  📁 Created directory: {path}")
        except Exception as e:
            if "already exists" not in str(e).lower():
                print(f"  ⚠️  Warning creating directory {path}: {e}")

    def upload_file(self, local_path: Path, remote_path: str, file_format: ImportFormat, language: Language = None):
        """Upload a single file to workspace"""
        try:
            with open(local_path, 'rb') as f:
                content = f.read()

            if self.dry_run:
                print(f"  [DRY RUN] Would upload: {local_path.name} → {remote_path}")
                self.stats["skipped"] += 1
                return

            self.w.workspace.upload(
                remote_path,
                content,
                format=file_format,
                overwrite=True
            )
            self.stats["uploaded"] += 1
            print(f"  ✅ Uploaded: {local_path.name} → {remote_path}")

        except Exception as e:
            self.stats["failed"] += 1
            print(f"  ❌ Failed to upload {local_path.name}: {e}")

    def sync_category(self, category: str, files: dict, source_dir: str = ""):
        """Sync a category of files"""
        print(f"\n📦 Syncing {category}...")

        # Create category directory
        category_path = f"{self.base_path}/{category}"
        self.create_directory(category_path)

        # Upload each file
        for filename, config in files.items():
            local_file = Path(source_dir) / filename if source_dir else Path(filename)

            if not local_file.exists():
                print(f"  ⚠️  File not found: {local_file}")
                self.stats["skipped"] += 1
                continue

            remote_path = f"{category_path}/{local_file.stem}"
            self.upload_file(
                local_file,
                remote_path,
                config["format"],
                config.get("language")
            )

    def sync_all(self):
        """Sync all files to workspace"""
        print(f"{'='*70}")
        print(f"🚀 Syncing Account Monitor to Databricks Workspace")
        print(f"{'='*70}")
        print(f"Profile: {self.profile}")
        print(f"User: {self.current_user.user_name}")
        print(f"Target: {self.base_path}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        print(f"{'='*70}")

        # Create base directory
        self.create_directory(self.base_path)

        # Sync notebooks
        self.sync_category("notebooks", FILES_TO_SYNC["notebooks"])

        # Sync SQL files
        self.sync_category("sql", FILES_TO_SYNC["sql"], "sql")

        # Sync documentation
        self.sync_category("docs", FILES_TO_SYNC["docs"])

        # Sync queries
        self.sync_category("queries", FILES_TO_SYNC["queries"])

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print sync summary"""
        print(f"\n{'='*70}")
        print(f"📊 Sync Summary")
        print(f"{'='*70}")
        print(f"✅ Uploaded: {self.stats['uploaded']}")
        print(f"⚠️  Skipped:  {self.stats['skipped']}")
        print(f"❌ Failed:   {self.stats['failed']}")
        print(f"{'='*70}")

        if self.stats['failed'] == 0:
            print(f"\n🎉 All files synced successfully!")
            print(f"\n📍 View in workspace:")
            print(f"   {self.w.config.host}/#workspace{self.base_path}")
        else:
            print(f"\n⚠️  Some files failed to sync. Check errors above.")

        print(f"\n📚 Next steps:")
        print(f"   1. Open workspace at: {self.base_path}")
        print(f"   2. Run post_deployment_validation notebook")
        print(f"   3. Review documentation in docs/")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Sync Account Monitor files to Databricks workspace"
    )
    parser.add_argument(
        "--profile",
        default=PROFILE,
        help=f"Databricks CLI profile (default: {PROFILE})"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced without uploading"
    )

    args = parser.parse_args()

    try:
        syncer = WorkspaceSync(profile=args.profile, dry_run=args.dry_run)
        syncer.sync_all()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"\nTroubleshooting:")
        print(f"  1. Verify profile is configured: databricks auth profiles")
        print(f"  2. Test connection: databricks workspace list --profile {args.profile} /")
        print(f"  3. Check permissions: You need workspace write access")
        sys.exit(1)


if __name__ == "__main__":
    main()
