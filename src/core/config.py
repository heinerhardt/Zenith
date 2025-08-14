"""
Configuration management for Zenith PDF Chatbot
Handles environment variables and application settings
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Authentication Configuration
    enable_auth: bool = Field(default=True, env="ENABLE_AUTH")
    jwt_secret_key: str = Field(default="zenith-jwt-secret-key", env="JWT_SECRET_KEY")
    session_duration_hours: int = Field(default=24, env="SESSION_DURATION_HOURS")
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    openai_embedding_model: str = Field(default="text-embedding-ada-002", env="OPENAI_EMBEDDING_MODEL")
    
    # Ollama Configuration
    ollama_enabled: bool = Field(default=False, env="OLLAMA_ENABLED")
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_chat_model: str = Field(default="llama2", env="OLLAMA_CHAT_MODEL")
    ollama_embedding_model: str = Field(default="nomic-embed-text", env="OLLAMA_EMBEDDING_MODEL")
    
    # Model Provider Selection
    chat_provider: str = Field(default="openai", env="CHAT_PROVIDER")  # openai or ollama
    embedding_provider: str = Field(default="openai", env="EMBEDDING_PROVIDER")  # openai or ollama
    
    # Langfuse Configuration (Self-hosted observability)
    langfuse_enabled: bool = Field(default=False, env="LANGFUSE_ENABLED")
    langfuse_host: str = Field(default="http://localhost:3000", env="LANGFUSE_HOST")
    langfuse_public_key: Optional[str] = Field(default=None, env="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: Optional[str] = Field(default=None, env="LANGFUSE_SECRET_KEY")
    langfuse_project_name: str = Field(default="zenith-pdf-chatbot", env="LANGFUSE_PROJECT_NAME")
    langfuse_tracing_enabled: bool = Field(default=True, env="LANGFUSE_TRACING_ENABLED")
    langfuse_evaluation_enabled: bool = Field(default=False, env="LANGFUSE_EVALUATION_ENABLED")
    
    # Qdrant Configuration
    qdrant_mode: str = Field(default="local", env="QDRANT_MODE")  # local or cloud
    qdrant_url: str = Field(default="localhost", env="QDRANT_URL")
    qdrant_port: int = Field(default=6333, env="QDRANT_PORT")
    qdrant_api_key: Optional[str] = Field(default=None, env="QDRANT_API_KEY")
    qdrant_collection_name: str = Field(default="zenith_documents", env="QDRANT_COLLECTION_NAME")
    qdrant_users_collection: str = Field(default="zenith_users", env="QDRANT_USERS_COLLECTION")
    
    # Text Processing Configuration
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    max_chunks_per_query: int = Field(default=5, env="MAX_CHUNKS_PER_QUERY")
    
    # Application Configuration
    app_port: int = Field(default=8501, env="APP_PORT")
    debug_mode: bool = Field(default=True, env="DEBUG_MODE")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # File Processing Configuration
    max_file_size_mb: int = Field(default=50, env="MAX_FILE_SIZE_MB")
    allowed_extensions: str = Field(default=".pdf", env="ALLOWED_EXTENSIONS")
    temp_dir: str = Field(default="temp_pdfs", env="TEMP_DIR")
    
    # Performance Configuration
    batch_size: int = Field(default=50, env="BATCH_SIZE")
    max_concurrent_requests: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS")
    memory_limit_gb: int = Field(default=8, env="MEMORY_LIMIT_GB")
    
    # Security Configuration
    cors_origins: str = Field(default="*", env="CORS_ORIGINS")
    api_key_required: bool = Field(default=False, env="API_KEY_REQUIRED")
    session_secret_key: str = Field(default="zenith-secret-key", env="SESSION_SECRET_KEY")
    
    # Monitoring Configuration
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=8502, env="METRICS_PORT")
    
    # MinIO Configuration (optional - for MinIO integration)
    minio_endpoint: Optional[str] = Field(default=None, env="MINIO_ENDPOINT")
    minio_access_key: Optional[str] = Field(default=None, env="MINIO_ACCESS_KEY")
    minio_secret_key: Optional[str] = Field(default=None, env="MINIO_SECRET_KEY")
    minio_secure: bool = Field(default=False, env="MINIO_SECURE")
    minio_region: str = Field(default="us-east-1", env="MINIO_REGION")
    
    # Batch Processing Configuration (optional)
    processing_timeout_minutes: int = Field(default=30, env="PROCESSING_TIMEOUT_MINUTES")
    max_concurrent_downloads: int = Field(default=5, env="MAX_CONCURRENT_DOWNLOADS")
    auto_cleanup_temp_files: bool = Field(default=True, env="AUTO_CLEANUP_TEMP_FILES")
    async_processing: bool = Field(default=True, env="ASYNC_PROCESSING")
    enable_processing_metrics: bool = Field(default=True, env="ENABLE_PROCESSING_METRICS")
    log_processing_details: bool = Field(default=True, env="LOG_PROCESSING_DETAILS")
    processing_log_level: str = Field(default="INFO", env="PROCESSING_LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def load_config() -> Settings:
    """
    Load configuration from environment variables and .env file
    
    Returns:
        Settings: Configuration object
    """
    # Get project root directory
    project_root = Path(__file__).parent.parent.parent
    env_path = project_root / ".env"
    
    # Load environment variables from .env file
    if env_path.exists():
        load_dotenv(env_path)
    
    return Settings()


def get_project_root() -> Path:
    """
    Get the project root directory
    
    Returns:
        Path: Project root path
    """
    return Path(__file__).parent.parent.parent


def get_data_dir() -> Path:
    """
    Get the data directory path
    
    Returns:
        Path: Data directory path
    """
    return get_project_root() / "data"


def get_logs_dir() -> Path:
    """
    Get the logs directory path
    
    Returns:
        Path: Logs directory path
    """
    return get_project_root() / "logs"


def get_temp_dir() -> Path:
    """
    Get the temporary directory path
    
    Returns:
        Path: Temporary directory path
    """
    return get_project_root() / "temp_pdfs"


# Global configuration instance
config = load_config()
