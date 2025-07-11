#!/usr/bin/env python3
"""
Release automation script for c2md package.
Handles version bumping, Git operations, and release creation.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional


class ReleaseManager:
    """Manages the release process for the c2md package."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.pyproject_path = repo_root / "pyproject.toml"
        self.init_path = repo_root / "c2md" / "__init__.py"

    def get_current_version(self) -> str:
        """Get the current version from c2md/__init__.py."""
        content = self.init_path.read_text()
        match = re.search(r'__version__ = ["\']([^"\']+)["\']', content)
        if not match:
            raise ValueError("Could not find version in c2md/__init__.py")
        return match.group(1)

    def bump_version(self, version_type: str) -> str:
        """Bump version using hatch."""
        cmd = ["hatch", "version", version_type]
        result = subprocess.run(cmd, cwd=self.repo_root, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to bump version: {result.stderr}")

        # Get the new version
        new_version = self.get_current_version()
        print(f"Version bumped to: {new_version}")
        return new_version

    def create_and_push_tag(self, version: str, message: Optional[str] = None) -> None:
        """Create and push a Git tag."""
        tag_name = f"v{version}"
        tag_message = message or f"Release {version}"

        # Create signed tag
        cmd = ["git", "tag", "-s", tag_name, "-m", tag_message]
        result = subprocess.run(cmd, cwd=self.repo_root)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create tag {tag_name}")

        # Push tag
        cmd = ["git", "push", "origin", tag_name]
        result = subprocess.run(cmd, cwd=self.repo_root)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to push tag {tag_name}")

        print(f"Created and pushed tag: {tag_name}")

    def commit_version_change(self, version: str) -> None:
        """Commit the version change."""
        # Add both files that hatch modifies during version bump
        cmd = ["git", "add", "c2md/__init__.py"]
        subprocess.run(cmd, cwd=self.repo_root, check=True)
        
        # Note: pyproject.toml doesn't change since it uses dynamic versioning,
        # but we'll add it just in case for future compatibility
        cmd = ["git", "add", "pyproject.toml"]
        subprocess.run(cmd, cwd=self.repo_root, check=True)

        cmd = ["git", "commit", "-m", f"chore: bump version to {version}"]
        subprocess.run(cmd, cwd=self.repo_root, check=True)

        print(f"Committed version change: {version}")

    def check_working_directory(self) -> None:
        """Check if working directory is clean."""
        cmd = ["git", "status", "--porcelain"]
        result = subprocess.run(cmd, cwd=self.repo_root, capture_output=True, text=True)
        if result.stdout.strip():
            raise RuntimeError("Working directory is not clean. Please commit or stash changes.")

    def run_tests(self) -> None:
        """Run tests before release."""
        print("Running tests...")
        cmd = ["hatch", "run", "test"]
        result = subprocess.run(cmd, cwd=self.repo_root)
        if result.returncode != 0:
            raise RuntimeError("Tests failed. Please fix issues before releasing.")
        print("Tests passed!")

    def create_release(self, version_type: str, message: Optional[str] = None,
                      skip_tests: bool = False) -> str:
        """Create a full release."""
        print(f"Creating {version_type} release...")

        # Check preconditions
        self.check_working_directory()

        if not skip_tests:
            self.run_tests()

        # Bump version
        new_version = self.bump_version(version_type)

        # Commit version change
        self.commit_version_change(new_version)

        # Create and push tag
        self.create_and_push_tag(new_version, message)

        # Push commits
        cmd = ["git", "push", "origin", "main"]
        subprocess.run(cmd, cwd=self.repo_root, check=True)

        print(f"Release {new_version} created successfully!")
        print("GitHub Actions will automatically build and publish to PyPI.")
        return new_version


def main():
    parser = argparse.ArgumentParser(description="Release automation for c2md")
    parser.add_argument("version_type", choices=["patch", "minor", "major"],
                       help="Type of version bump")
    parser.add_argument("-m", "--message", help="Release message")
    parser.add_argument("--skip-tests", action="store_true",
                       help="Skip running tests before release")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be done without executing")

    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    manager = ReleaseManager(repo_root)

    try:
        if args.dry_run:
            current_version = manager.get_current_version()
            print(f"Current version: {current_version}")
            print(f"Would create {args.version_type} release")
            print("Use --no-dry-run to execute")
        else:
            manager.create_release(args.version_type, args.message, args.skip_tests)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
