# cache_manager.py
import os
import json
import hashlib
import time
from typing import Dict, Optional, Tuple, List
from urllib.parse import urlparse
from datetime import datetime, timedelta
from config import get_config

class RepositoryCache:
    """Manages caching of repository metadata and indexing status."""

    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = cache_dir
        self.metadata_file = os.path.join(cache_dir, "repo_metadata.json")
        self.ensure_cache_dir()
        self.metadata = self.load_metadata()

    def ensure_cache_dir(self):
        """Ensure cache directory exists."""
        os.makedirs(self.cache_dir, exist_ok=True)

    def load_metadata(self) -> Dict:
        """Load repository metadata from cache."""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save_metadata(self):
        """Save repository metadata to cache."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2, default=str)

    def get_repo_hash(self, repo_url: str) -> str:
        """Generate a unique hash for the repository URL."""
        return hashlib.md5(repo_url.encode()).hexdigest()[:8]

    def get_repo_info(self, repo_url: str) -> Optional[Dict]:
        """Get cached information for a repository."""
        repo_hash = self.get_repo_hash(repo_url)
        return self.metadata.get(repo_hash)

    def is_repo_cached(self, repo_url: str, max_age_days: int = 7) -> bool:
        """Check if repository is cached and not too old."""
        repo_info = self.get_repo_info(repo_url)
        if not repo_info:
            return False

        # Check if cache is expired
        cached_time = datetime.fromisoformat(repo_info.get('last_indexed', '2000-01-01'))
        if datetime.now() - cached_time > timedelta(days=max_age_days):
            return False

        # Check if vector database still exists
        db_path = repo_info.get('db_path')
        if not db_path or not os.path.exists(db_path):
            return False

        return True

    def update_repo_cache(self, repo_url: str, repo_path: str, db_path: str,
                         file_count: int, chunk_count: int, languages: Dict[str, int]):
        """Update cache information for a repository."""
        repo_hash = self.get_repo_hash(repo_url)
        repo_name = self.extract_repo_name(repo_url)

        self.metadata[repo_hash] = {
            'repo_url': repo_url,
            'repo_name': repo_name,
            'repo_hash': repo_hash,
            'repo_path': repo_path,
            'db_path': db_path,
            'file_count': file_count,
            'chunk_count': chunk_count,
            'languages': languages,
            'last_indexed': datetime.now().isoformat(),
            'indexed_at': time.time()
        }

        self.save_metadata()

    def extract_repo_name(self, repo_url: str) -> str:
        """Extract repository name from URL."""
        parsed = urlparse(repo_url)
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) >= 2:
            return f"{path_parts[-2]}/{path_parts[-1]}"
        return "unknown"

    def get_cache_stats(self) -> Dict:
        """Get statistics about cached repositories."""
        total_repos = len(self.metadata)
        total_files = sum(repo.get('file_count', 0) for repo in self.metadata.values())
        total_chunks = sum(repo.get('chunk_count', 0) for repo in self.metadata.values())

        # Get language breakdown
        all_languages = {}
        for repo in self.metadata.values():
            for lang, count in repo.get('languages', {}).items():
                all_languages[lang] = all_languages.get(lang, 0) + count

        return {
            'cached_repositories': total_repos,
            'total_files': total_files,
            'total_chunks': total_chunks,
            'language_breakdown': all_languages
        }

    def clear_expired_cache(self, max_age_days: int = 30):
        """Clear expired cache entries."""
        current_time = datetime.now()
        expired_hashes = []

        for repo_hash, repo_info in self.metadata.items():
            cached_time = datetime.fromisoformat(repo_info.get('last_indexed', '2000-01-01'))
            if current_time - cached_time > timedelta(days=max_age_days):
                expired_hashes.append(repo_hash)

        for repo_hash in expired_hashes:
            del self.metadata[repo_hash]

        if expired_hashes:
            self.save_metadata()

    def get_recent_repos(self, limit: int = 5) -> List[Dict]:
        """Get recently indexed repositories."""
        repos = list(self.metadata.values())
        repos.sort(key=lambda x: x.get('indexed_at', 0), reverse=True)
        return repos[:limit]

# Global cache instance
_cache_instance = None

def get_cache_manager() -> RepositoryCache:
    """Get the global cache manager instance."""
    global _cache_instance
    if _cache_instance is None:
        config = get_config()
        _cache_instance = RepositoryCache(config.cache_dir)
    return _cache_instance

def check_repo_cache(repo_url: str) -> Tuple[bool, Optional[Dict]]:
    """Check if repository is cached and return cache info."""
    cache = get_cache_manager()
    is_cached = cache.is_repo_cached(repo_url)
    repo_info = cache.get_repo_info(repo_url) if is_cached else None
    return is_cached, repo_info

def update_repo_cache(repo_url: str, repo_path: str, db_path: str,
                     file_count: int, chunk_count: int, languages: Dict[str, int]):
    """Update repository cache information."""
    cache = get_cache_manager()
    cache.update_repo_cache(repo_url, repo_path, db_path, file_count, chunk_count, languages)

if __name__ == "__main__":
    # Example usage
    cache = get_cache_manager()

    # Test cache operations
    test_url = "https://github.com/pallets/flask"
    print(f"Repo hash for {test_url}: {cache.get_repo_hash(test_url)}")

    # Show cache stats
    stats = cache.get_cache_stats()
    print("Cache statistics:", stats)
