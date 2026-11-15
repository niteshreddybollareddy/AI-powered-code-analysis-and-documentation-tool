# logger.py
import logging
import logging.handlers
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from config import get_config

class CodebaseOracleLogger:
    """Comprehensive logging system for Codebase Oracle."""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.ensure_log_dir()
        self.setup_loggers()

    def ensure_log_dir(self):
        """Ensure log directory exists."""
        os.makedirs(self.log_dir, exist_ok=True)

    def setup_loggers(self):
        """Set up multiple loggers for different components."""
        # Main application logger
        self.app_logger = logging.getLogger('codebase_oracle.app')
        self.app_logger.setLevel(logging.INFO)

        # Indexing logger
        self.index_logger = logging.getLogger('codebase_oracle.indexing')
        self.index_logger.setLevel(logging.INFO)

        # Query logger
        self.query_logger = logging.getLogger('codebase_oracle.query')
        self.query_logger.setLevel(logging.INFO)

        # Error logger
        self.error_logger = logging.getLogger('codebase_oracle.error')
        self.error_logger.setLevel(logging.WARNING)

        # Performance logger
        self.perf_logger = logging.getLogger('codebase_oracle.performance')
        self.perf_logger.setLevel(logging.INFO)

        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )

        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )

        # Create handlers
        self._setup_file_handlers(detailed_formatter, simple_formatter)
        self._setup_console_handlers(simple_formatter)

    def _setup_file_handlers(self, detailed_formatter, simple_formatter):
        """Set up file logging handlers."""
        # Rotating file handler for all logs
        all_logs_handler = logging.handlers.RotatingFileHandler(
            os.path.join(self.log_dir, 'codebase_oracle.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        all_logs_handler.setFormatter(detailed_formatter)
        all_logs_handler.setLevel(logging.DEBUG)

        # Separate error log
        error_handler = logging.handlers.RotatingFileHandler(
            os.path.join(self.log_dir, 'errors.log'),
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setFormatter(detailed_formatter)
        error_handler.setLevel(logging.ERROR)

        # Performance log
        perf_handler = logging.FileHandler(
            os.path.join(self.log_dir, 'performance.log')
        )
        perf_handler.setFormatter(simple_formatter)

        # Add handlers to loggers
        for logger in [self.app_logger, self.index_logger, self.query_logger, self.error_logger, self.perf_logger]:
            logger.addHandler(all_logs_handler)
            logger.addHandler(error_handler)

        self.perf_logger.addHandler(perf_handler)

    def _setup_console_handlers(self, simple_formatter):
        """Set up console logging handlers."""
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(simple_formatter)
        console_handler.setLevel(logging.INFO)

        # Add console handler to main loggers
        self.app_logger.addHandler(console_handler)
        self.error_logger.addHandler(console_handler)

    # Logging methods
    def log_app_start(self):
        """Log application startup."""
        self.app_logger.info("🚀 Codebase Oracle application started")

    def log_repo_indexing_start(self, repo_url: str):
        """Log start of repository indexing."""
        self.index_logger.info(f"📥 Starting indexing of repository: {repo_url}")

    def log_repo_indexing_complete(self, repo_url: str, stats: Dict[str, Any]):
        """Log completion of repository indexing."""
        self.index_logger.info(
            f"✅ Completed indexing of {repo_url}: "
            f"{stats.get('file_count', 0)} files, "
            f"{stats.get('chunk_count', 0)} chunks, "
            f"{len(stats.get('languages', {}))} languages"
        )

    def log_query(self, question: str, response_length: int, processing_time: float):
        """Log query processing."""
        self.query_logger.info(
            f"🤔 Query processed - Length: {len(question)} chars, "
            f"Response: {response_length} chars, "
            f"Time: {processing_time:.2f}s"
        )

    def log_performance(self, operation: str, duration: float, metadata: Optional[Dict] = None):
        """Log performance metrics."""
        metadata_str = f" - {json.dumps(metadata)}" if metadata else ""
        self.perf_logger.info(
            f"⚡ {operation}: {duration:.2f}s{metadata_str}"
        )

    def log_error(self, error: Exception, context: str = ""):
        """Log errors with context."""
        self.error_logger.error(
            f"❌ Error in {context}: {str(error)}",
            exc_info=True
        )

    def log_cache_hit(self, repo_url: str):
        """Log cache hits."""
        self.app_logger.info(f"💾 Cache hit for repository: {repo_url}")

    def log_cache_miss(self, repo_url: str):
        """Log cache misses."""
        self.app_logger.info(f"🔄 Cache miss for repository: {repo_url}")

    def get_recent_logs(self, lines: int = 50) -> str:
        """Get recent log entries."""
        log_file = os.path.join(self.log_dir, 'codebase_oracle.log')
        if not os.path.exists(log_file):
            return "No logs available"

        try:
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                return ''.join(all_lines[-lines:])
        except Exception as e:
            return f"Error reading logs: {e}"

    def get_error_logs(self, lines: int = 20) -> str:
        """Get recent error log entries."""
        error_file = os.path.join(self.log_dir, 'errors.log')
        if not os.path.exists(error_file):
            return "No error logs available"

        try:
            with open(error_file, 'r') as f:
                all_lines = f.readlines()
                return ''.join(all_lines[-lines:])
        except Exception as e:
            return f"Error reading error logs: {e}"

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics from logs."""
        perf_file = os.path.join(self.log_dir, 'performance.log')
        if not os.path.exists(perf_file):
            return {"error": "Performance log not found"}

        stats = {
            "total_operations": 0,
            "avg_duration": 0,
            "operation_counts": {},
            "durations": []
        }

        try:
            with open(perf_file, 'r') as f:
                for line in f:
                    if "⚡" in line:
                        parts = line.split("⚡")[1].split(":")
                        if len(parts) >= 2:
                            operation = parts[0].strip()
                            duration_str = parts[1].split("s")[0].strip()

                            try:
                                duration = float(duration_str)
                                stats["total_operations"] += 1
                                stats["durations"].append(duration)
                                stats["operation_counts"][operation] = stats["operation_counts"].get(operation, 0) + 1
                            except ValueError:
                                continue

            if stats["durations"]:
                stats["avg_duration"] = sum(stats["durations"]) / len(stats["durations"])
                stats["max_duration"] = max(stats["durations"])
                stats["min_duration"] = min(stats["durations"])

        except Exception as e:
            stats["error"] = str(e)

        return stats

# Global logger instance
_logger = None

def get_logger() -> CodebaseOracleLogger:
    """Get the global logger instance."""
    global _logger
    if _logger is None:
        config = get_config()
        _logger = CodebaseOracleLogger(config.logs_dir)
    return _logger

# Convenience functions
def log_app_start():
    """Log application startup."""
    get_logger().log_app_start()

def log_repo_indexing_start(repo_url: str):
    """Log start of repository indexing."""
    get_logger().log_repo_indexing_start(repo_url)

def log_repo_indexing_complete(repo_url: str, stats: Dict[str, Any]):
    """Log completion of repository indexing."""
    get_logger().log_repo_indexing_complete(repo_url, stats)

def log_query(question: str, response_length: int, processing_time: float):
    """Log query processing."""
    get_logger().log_query(question, response_length, processing_time)

def log_performance(operation: str, duration: float, metadata: Optional[Dict] = None):
    """Log performance metrics."""
    get_logger().log_performance(operation, duration, metadata)

def log_error(error: Exception, context: str = ""):
    """Log errors with context."""
    get_logger().log_error(error, context)

def log_cache_hit(repo_url: str):
    """Log cache hits."""
    get_logger().log_cache_hit(repo_url)

def log_cache_miss(repo_url: str):
    """Log cache misses."""
    get_logger().log_cache_miss(repo_url)

if __name__ == "__main__":
    # Example usage
    logger = CodebaseOracleLogger()

    logger.log_app_start()
    logger.log_repo_indexing_start("https://github.com/pallets/flask")
    logger.log_performance("chunking", 2.34, {"files": 150, "chunks": 1200})
    logger.log_query("How does Flask handle routing?", 450, 1.2)

    print("Sample logs created. Check logs/ directory.")
