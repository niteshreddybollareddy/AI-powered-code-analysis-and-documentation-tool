# config.py
import os
from typing import Dict, List, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

@dataclass
class LanguageConfig:
    """Configuration for language-specific processing."""
    extensions: List[str]
    chunker: str
    chunk_size: int
    chunk_overlap: int
    language: str = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'extensions': self.extensions,
            'chunker': self.chunker,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'language': self.language
        }

@dataclass
class ModelConfig:
    """Configuration for AI models and embeddings."""
    embedding_model: str = "all-MiniLM-L6-v2"
    llm_model: str = "gpt-3.5-turbo"
    temperature: float = 0.1
    max_tokens: int = 1000
    top_k: int = 5

@dataclass
class IndexingConfig:
    """Configuration for repository indexing."""
    supported_extensions: List[str] = field(default_factory=lambda: [
        '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.cc', '.cxx',
        '.hpp', '.hxx', '.go', '.rs', '.md', '.markdown', '.json', '.yaml',
        '.yml', '.html', '.htm', '.xml', '.txt', '.log'
    ])
    exclude_dirs: List[str] = field(default_factory=lambda: [
        '.git', 'node_modules', '__pycache__', '.venv', 'venv', 'env',
        'dist', 'build', '.next', '.nuxt'
    ])
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    max_files: int = 1000

@dataclass
class UIConfig:
    """Configuration for user interface."""
    page_title: str = "Codebase Oracle"
    page_icon: str = "🤖"
    layout: str = "wide"
    theme: str = "light"

@dataclass
class Config:
    """Main configuration class."""
    # Directory paths
    repo_dir: str = "temp_repo"
    db_dir: str = "chroma_db_code"
    cache_dir: str = ".cache"
    logs_dir: str = "logs"

    # API keys
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))

    # Sub-configurations
    model: ModelConfig = field(default_factory=ModelConfig)
    indexing: IndexingConfig = field(default_factory=IndexingConfig)
    ui: UIConfig = field(default_factory=UIConfig)

    # Language configurations
    languages: Dict[str, LanguageConfig] = field(default_factory=lambda: {
        'python': LanguageConfig(
            extensions=['.py', '.pyx', '.pyi'],
            chunker='ast',
            chunk_size=1500,
            chunk_overlap=150
        ),
        'javascript': LanguageConfig(
            extensions=['.js', '.jsx', '.mjs'],
            chunker='langchain',
            chunk_size=1200,
            chunk_overlap=120,
            language='js'
        ),
        'typescript': LanguageConfig(
            extensions=['.ts', '.tsx'],
            chunker='langchain',
            chunk_size=1200,
            chunk_overlap=120,
            language='js'
        ),
        'java': LanguageConfig(
            extensions=['.java'],
            chunker='langchain',
            chunk_size=1400,
            chunk_overlap=140,
            language='java'
        ),
        'cpp': LanguageConfig(
            extensions=['.cpp', '.cc', '.cxx', '.c++', '.hpp', '.hxx', '.h++'],
            chunker='langchain',
            chunk_size=1300,
            chunk_overlap=130,
            language='cpp'
        ),
        'go': LanguageConfig(
            extensions=['.go'],
            chunker='langchain',
            chunk_size=1400,
            chunk_overlap=140,
            language='go'
        ),
        'rust': LanguageConfig(
            extensions=['.rs'],
            chunker='langchain',
            chunk_size=1400,
            chunk_overlap=140,
            language='rust'
        ),
        'markdown': LanguageConfig(
            extensions=['.md', '.markdown'],
            chunker='text',
            chunk_size=1000,
            chunk_overlap=100
        ),
        'json': LanguageConfig(
            extensions=['.json', '.yaml', '.yml', '.toml'],
            chunker='text',
            chunk_size=800,
            chunk_overlap=80
        ),
        'html': LanguageConfig(
            extensions=['.html', '.htm', '.xml'],
            chunker='text',
            chunk_size=900,
            chunk_overlap=90
        ),
        'text': LanguageConfig(
            extensions=['.txt', '.log', '.ini', '.cfg'],
            chunker='text',
            chunk_size=1000,
            chunk_overlap=100
        )
    })

    def validate(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []

        if not self.openai_api_key:
            issues.append("OPENAI_API_KEY environment variable is not set")

        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)

        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir, exist_ok=True)

        return issues

    def save_to_env(self, file_path: str = ".env"):
        """Save configuration to .env file."""
        env_content = f"""# Codebase Oracle Configuration
OPENAI_API_KEY={self.openai_api_key}

# Model Configuration
EMBEDDING_MODEL={self.model.embedding_model}
LLM_MODEL={self.model.llm_model}
TEMPERATURE={self.model.temperature}
MAX_TOKENS={self.model.max_tokens}
TOP_K={self.model.top_k}

# Indexing Configuration
MAX_FILE_SIZE={self.indexing.max_file_size}
MAX_FILES={self.indexing.max_files}
"""
        with open(file_path, 'w') as f:
            f.write(env_content)

# Global configuration instance
config = Config()

def get_config() -> Config:
    """Get the global configuration instance."""
    return config

def update_config(updates: Dict[str, Any]) -> Config:
    """Update configuration with new values."""
    for key, value in updates.items():
        if hasattr(config, key):
            setattr(config, key, value)
    return config

def load_config_from_env() -> Config:
    """Load configuration from environment variables."""
    # Update from environment variables
    config.openai_api_key = os.getenv("OPENAI_API_KEY", config.openai_api_key)
    config.model.embedding_model = os.getenv("EMBEDDING_MODEL", config.model.embedding_model)
    config.model.llm_model = os.getenv("LLM_MODEL", config.model.llm_model)
    config.model.temperature = float(os.getenv("TEMPERATURE", config.model.temperature))
    config.model.max_tokens = int(os.getenv("MAX_TOKENS", config.model.max_tokens))
    config.model.top_k = int(os.getenv("TOP_K", config.model.top_k))
    config.indexing.max_file_size = int(os.getenv("MAX_FILE_SIZE", config.indexing.max_file_size))
    config.indexing.max_files = int(os.getenv("MAX_FILES", config.indexing.max_files))

    return config
