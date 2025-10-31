"""
Dynamic GitHub documentation and examples fetcher.

This module fetches documentation and examples from GitHub repositories
instead of hard-copying them into the project.
"""

import json
import shutil
import urllib.request
from pathlib import Path
from typing import Optional
from zipfile import ZipFile

from jutulgpt.cli import colorscheme, print_to_console


class GitHubRepoFetcher:
    """Fetches files from a GitHub repository."""

    def __init__(
        self,
        repo_owner: str,
        repo_name: str,
        cache_dir: Path,
        branch: str = "main",
    ):
        """
        Initialize the GitHub fetcher.

        Args:
            repo_owner: GitHub repository owner (e.g., 'sintefmath')
            repo_name: GitHub repository name (e.g., 'JutulDarcy.jl')
            cache_dir: Directory to cache downloaded files
            branch: Git branch to fetch from (default: 'main')
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.branch = branch
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Metadata file to track versions and downloads
        self.metadata_file = self.cache_dir / "metadata.json"

    @property
    def repo_url(self) -> str:
        """Get the repository URL."""
        return f"https://github.com/{self.repo_owner}/{self.repo_name}"

    @property
    def archive_url(self) -> str:
        """Get the archive download URL."""
        return f"{self.repo_url}/archive/refs/heads/{self.branch}.zip"

    def _get_remote_commit_sha(self) -> Optional[str]:
        """
        Get the latest commit SHA from the remote repository.

        Returns:
            The commit SHA or None if unable to fetch
        """
        api_url = (
            f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}"
            f"/commits/{self.branch}"
        )

        try:
            with urllib.request.urlopen(api_url, timeout=10) as response:
                data = json.loads(response.read().decode())
                return data["sha"]
        except Exception as e:
            print_to_console(
                text=f"Could not fetch remote commit SHA: {e}",
                title="GitHub Fetcher",
                border_style=colorscheme.warning,
            )
            return None

    def _get_installed_package_version(self) -> Optional[str]:
        """
        Get the version of the installed Julia package.

        Returns:
            Version string or None if not installed
        """
        from jutulgpt.julia.julia_code_runner import run_code_string_direct

        code = f"""
        using Pkg
        deps = Pkg.dependencies()
        jutuldarcy_uuid = findfirst(p -> p.name == "{self.repo_name.replace('.jl', '')}", deps)
        if jutuldarcy_uuid !== nothing
            version = deps[jutuldarcy_uuid].version
            println(version)
        else
            println("NOT_INSTALLED")
        end
        """

        try:
            result, _ = run_code_string_direct(code)
            version = result.strip()
            return version if version != "NOT_INSTALLED" else None
        except Exception as e:
            print_to_console(
                text=f"Could not get installed package version: {e}",
                title="GitHub Fetcher",
                border_style=colorscheme.warning,
            )
            return None

    def _load_metadata(self) -> dict:
        """Load metadata from cache."""
        if self.metadata_file.exists():
            with open(self.metadata_file, "r") as f:
                return json.load(f)
        return {}

    def _save_metadata(self, metadata: dict):
        """Save metadata to cache."""
        with open(self.metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

    def _needs_update(self, force: bool = False) -> bool:
        """
        Check if the cached files need to be updated.

        Args:
            force: Force update regardless of cache state

        Returns:
            True if update is needed
        """
        if force:
            return True

        metadata = self._load_metadata()

        if not metadata:
            return True

        # Check if commit SHA has changed
        remote_sha = self._get_remote_commit_sha()
        if remote_sha and metadata.get("commit_sha") != remote_sha:
            print_to_console(
                text=f"Remote repository has updates (SHA: {remote_sha[:8]})",
                title="GitHub Fetcher",
                border_style=colorscheme.message,
            )
            return True

        # Check if installed package version has changed
        installed_version = self._get_installed_package_version()
        if (
            installed_version
            and metadata.get("package_version") != installed_version
        ):
            print_to_console(
                text=f"Installed package version changed: {installed_version}",
                title="GitHub Fetcher",
                border_style=colorscheme.message,
            )
            return True

        return False

    def fetch(
        self,
        subdirs: list[str],
        force: bool = False,
        check_updates: bool = True,
    ) -> dict[str, Path]:
        """
        Fetch specific subdirectories from the repository.

        Args:
            subdirs: List of subdirectory paths to fetch (e.g., ['docs/man', 'examples'])
            force: Force re-download even if cache exists
            check_updates: Check for updates before using cache

        Returns:
            Dictionary mapping subdirectory names to their local paths
        """
        if check_updates and self._needs_update(force):
            self._download_and_extract(subdirs)

        # Verify all subdirectories exist
        results = {}
        for subdir in subdirs:
            local_path = self.cache_dir / subdir
            if not local_path.exists():
                # If any subdir is missing, download everything
                self._download_and_extract(subdirs)
                break
            results[subdir] = local_path
        else:
            # All subdirs exist
            return results

        # After download, build results
        for subdir in subdirs:
            local_path = self.cache_dir / subdir
            if local_path.exists():
                results[subdir] = local_path
            else:
                print_to_console(
                    text=f"Warning: Subdirectory '{subdir}' not found in repository",
                    title="GitHub Fetcher",
                    border_style=colorscheme.warning,
                )

        return results

    def _download_and_extract(self, subdirs: list[str]):
        """Download repository archive and extract specific subdirectories."""
        print_to_console(
            text=f"Downloading {self.repo_name} from GitHub...",
            title="GitHub Fetcher",
            border_style=colorscheme.message,
        )

        # Download archive
        archive_path = self.cache_dir / f"{self.repo_name}.zip"
        try:
            urllib.request.urlretrieve(self.archive_url, archive_path)
        except Exception as e:
            print_to_console(
                text=f"Failed to download repository: {e}",
                title="GitHub Fetcher",
                border_style=colorscheme.error,
            )
            raise

        # Extract specific subdirectories
        try:
            with ZipFile(archive_path, "r") as zip_file:
                # The archive contains a root folder like 'JutulDarcy.jl-main/'
                root_folder = zip_file.namelist()[0].split("/")[0]

                for subdir in subdirs:
                    # Clean up old directory if it exists
                    target_dir = self.cache_dir / subdir
                    if target_dir.exists():
                        shutil.rmtree(target_dir)

                    # Extract files from this subdirectory
                    prefix = f"{root_folder}/{subdir}/"
                    for file_info in zip_file.filelist:
                        if file_info.filename.startswith(prefix):
                            # Calculate relative path
                            rel_path = file_info.filename[len(f"{root_folder}/") :]
                            target_path = self.cache_dir / rel_path

                            if file_info.is_dir():
                                target_path.mkdir(parents=True, exist_ok=True)
                            else:
                                target_path.parent.mkdir(parents=True, exist_ok=True)
                                with zip_file.open(file_info) as source:
                                    with open(target_path, "wb") as target:
                                        target.write(source.read())

            print_to_console(
                text=f"Successfully extracted {len(subdirs)} subdirectories",
                title="GitHub Fetcher",
                border_style=colorscheme.success,
            )

        except Exception as e:
            print_to_console(
                text=f"Failed to extract archive: {e}",
                title="GitHub Fetcher",
                border_style=colorscheme.error,
            )
            raise
        finally:
            # Clean up archive
            if archive_path.exists():
                archive_path.unlink()

        # Update metadata
        metadata = {
            "commit_sha": self._get_remote_commit_sha(),
            "package_version": self._get_installed_package_version(),
            "repo_owner": self.repo_owner,
            "repo_name": self.repo_name,
            "branch": self.branch,
            "subdirs": subdirs,
        }
        self._save_metadata(metadata)
        
        # Clear vector stores to force re-indexing with new content
        self.clear_vector_stores()

    def get_cached_path(self, subdir: str) -> Optional[Path]:
        """
        Get the cached path for a subdirectory without fetching.

        Args:
            subdir: Subdirectory path

        Returns:
            Path to cached directory or None if not cached
        """
        path = self.cache_dir / subdir
        return path if path.exists() else None

    def clear_cache(self):
        """Clear all cached files."""
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            print_to_console(
                text="Cache cleared successfully",
                title="GitHub Fetcher",
                border_style=colorscheme.success,
            )

    def clear_vector_stores(self):
        """
        Clear vector stores associated with this repository.
        
        This should be called when documentation is updated to force
        re-indexing with the new content.
        """
        from jutulgpt.configuration import PROJECT_ROOT

        cache_root = PROJECT_ROOT.parent / ".cache"
        
        # Clear vector stores
        vector_store_patterns = [
            cache_root / "retriever_store" / f"retriever_{self.repo_name.replace('.jl', '').lower()}_*",
            cache_root / "loaded_store" / f"loaded_{self.repo_name.replace('.jl', '').lower()}_*.pkl",
        ]
        
        cleared_count = 0
        for pattern in vector_store_patterns:
            parent_dir = pattern.parent
            if parent_dir.exists():
                # Get the pattern as a glob string
                pattern_str = pattern.name
                for path in parent_dir.glob(pattern_str):
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    cleared_count += 1
        
        if cleared_count > 0:
            print_to_console(
                text=f"Cleared {cleared_count} vector store(s)",
                title="GitHub Fetcher",
                border_style=colorscheme.success,
            )


def get_jutuldarcy_fetcher(cache_root: Optional[Path] = None) -> GitHubRepoFetcher:
    """
    Get a GitHubRepoFetcher configured for JutulDarcy.jl.

    Args:
        cache_root: Root directory for cache (default: PROJECT_ROOT / ".cache")

    Returns:
        Configured GitHubRepoFetcher instance
    """
    if cache_root is None:
        from jutulgpt.configuration import PROJECT_ROOT

        cache_root = PROJECT_ROOT.parent / ".cache"

    cache_dir = cache_root / "jutuldarcy"

    return GitHubRepoFetcher(
        repo_owner="sintefmath",
        repo_name="JutulDarcy.jl",
        cache_dir=cache_dir,
        branch="main",
    )
