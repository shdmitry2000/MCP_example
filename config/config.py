import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional
from langfuse import Langfuse

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    """Centralized configuration management."""
    
    def __init__(self):
        # Get the project root directory - going up two levels from this file
        self.SRC_DIR = Path(__file__).parent.resolve()
        self.PROJECT_ROOT = self.SRC_DIR.parent.resolve()
        
        # Load environment variables from .env file
        self.ENV_FILE = self.PROJECT_ROOT / ".env"
        logger.info(f"Looking for .env file at: {self.ENV_FILE}")
        
        if self.ENV_FILE.exists():
            logger.info(".env file found")
            load_dotenv(str(self.ENV_FILE))
        else:
            logger.warning(f".env file not found at {self.ENV_FILE}")
            # Try to find .env in current working directory
            cwd_env = Path.cwd() / ".env"
            if cwd_env.exists():
                logger.info(f"Found .env file in current working directory: {cwd_env}")
                load_dotenv(str(cwd_env))
            else:
                logger.warning("No .env file found in current working directory either")
        
        # Load all configurations
        self._load_config()
        
        # Log loaded configuration (excluding sensitive data)
        self._log_config()
    
    def _load_config(self):
        """Load all configuration values."""
        # OpenAI Configuration
        self.OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
        self.OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.OPENAI_API_TYPE: str = os.getenv("OPENAI_API_TYPE", "openai")
        self.OPENAI_API_VERSION: str = os.getenv("OPENAI_API_VERSION", "2023-05-15")
        
        # Google Cloud Configuration
        self.GOOGLE_CLOUD_PROJECT_ID: str = os.getenv("GOOGLE_CLOUD_PROJECT_ID", "me-sb-dgcp-dpoc-pocyosh-pr")
        self.VERTEX_LOCATION: str = os.getenv("VERTEX_LOCATION", "us-central1")  # For Gemini models
        self.ANTHROPIC_VERTEX_LOCATION: str = os.getenv("ANTHROPIC_VERTEX_LOCATION", "us-east4")  # For Anthropic models
        self.GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
        
        # Gemini Model Configuration
        self.GEMINI_LLM_MODEL_NAME: str = os.getenv("GEMINI_LLM_MODEL_NAME", "gemini-2.0-flash-001")
        self.GEMINI_LLM_REASONER_MODEL: str = os.getenv("GEMINI_LLM_REASONER_MODEL", "gemini-2.5-pro-preview-03-25")
        
        # Anthropic Model Configuration
        self.ANTHROPIC_LLM_MODEL_NAME: str = os.getenv("ANTHROPIC_LLM_MODEL_NAME", "claude-3-sonnet-20240229")
        self.ANTHROPIC_LLM_REASONER_MODEL: str = os.getenv("ANTHROPIC_LLM_REASONER_MODEL", "claude-3-7-sonnet@20250219")
        
        # MCP Server Configuration
        self.MCP_SERVER_MODE: str = os.getenv("MCP_SERVER_MODE", "local")  # 'local' or 'remote'
        self.MCP_SERVER_HOST: str = os.getenv("MCP_SERVER_HOST", "localhost")
        self.MCP_SERVER_PORT: int = int(os.getenv("MCP_SERVER_PORT", "8000"))
        self.MCP_SERVER_URL: str = f"http://{self.MCP_SERVER_HOST}:{self.MCP_SERVER_PORT}"
        
        # Langfuse Configuration
        self.LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
        self.LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY", "")
        self.LANGFUSE_HOST: str = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        
        # Langfuse OTEL Configuration
        if self.LANGFUSE_PUBLIC_KEY and self.LANGFUSE_SECRET_KEY:
            import base64
            self.LANGFUSE_AUTH = base64.b64encode(
                f"{self.LANGFUSE_PUBLIC_KEY}:{self.LANGFUSE_SECRET_KEY}".encode()
            ).decode()
            
            # Set OTEL environment variables
            os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"{self.LANGFUSE_HOST}/api/public/otel"
            os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {self.LANGFUSE_AUTH}"
        
        # Logfire Configuration
        self.LOGFIRE_SERVICE_NAME: str = os.getenv("LOGFIRE_SERVICE_NAME", "dbank-cc")
        self.LOGFIRE_SEND_TO_LOGFIRE: bool = os.getenv("LOGFIRE_SEND_TO_LOGFIRE", "False").lower() == "true"
        
        # Configure Logfire if available
        try:
            import logfire
            if hasattr(logfire, 'configure'):
                logfire.configure(
                    service_name=self.LOGFIRE_SERVICE_NAME,
                    send_to_logfire=self.LOGFIRE_SEND_TO_LOGFIRE,
                )
        except (ImportError, AttributeError) as e:
            logger.warning(f"Logfire configuration skipped: {str(e)}")
        
        # Initialize Langfuse
        if self.LANGFUSE_PUBLIC_KEY and self.LANGFUSE_SECRET_KEY:
            self.langfuse = Langfuse(
                public_key=self.LANGFUSE_PUBLIC_KEY,
                secret_key=self.LANGFUSE_SECRET_KEY,
                host=self.LANGFUSE_HOST
            )
        else:
            self.langfuse = None
        
        
        # Database Configuration
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "")
        
        # Application Configuration
        self.DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///default_database.db")
    
        # Database folder configuration
        self.DB_FOLDER: str = os.getenv("DB_FOLDER", "database_files")
        self.DEFAULT_DB_NAME: str = os.getenv("DEFAULT_DB_NAME", "generated_data")
        
        # Ensure DB folder exists
        Path(self.DB_FOLDER).mkdir(parents=True, exist_ok=True)
        
        # Update DATABASE_URL to use DB_FOLDER if it's a SQLite database
        if self.DATABASE_URL.startswith("sqlite:///") and not os.path.isabs(self.DATABASE_URL.replace("sqlite:///", "")):
            db_filename = self.DATABASE_URL.replace("sqlite:///", "")
            self.DATABASE_URL = f"sqlite:///{self.DB_FOLDER}/{db_filename}"
    
    
    
    def _log_config(self):
        """Log non-sensitive configuration values."""
        logger.info("Loaded configuration:")
        logger.info(f"OPENAI_API_BASE: {self.OPENAI_API_BASE}")
        logger.info(f"OPENAI_API_TYPE: {self.OPENAI_API_TYPE}")
        logger.info(f"OPENAI_API_VERSION: {self.OPENAI_API_VERSION}")
        logger.info(f"OPENAI_API_KEY present: {'Yes' if self.OPENAI_API_KEY else 'No'}")
        logger.info(f"GOOGLE_CLOUD_PROJECT_ID: {self.GOOGLE_CLOUD_PROJECT_ID}")
        logger.info(f"VERTEX_LOCATION (Gemini): {self.VERTEX_LOCATION}")
        logger.info(f"VERTEX_LOCATION (Anthropic): {self.ANTHROPIC_VERTEX_LOCATION}")
        logger.info(f"GEMINI_LLM_MODEL_NAME: {self.GEMINI_LLM_MODEL_NAME}")
        logger.info(f"ANTHROPIC_LLM_MODEL_NAME: {self.ANTHROPIC_LLM_MODEL_NAME}")
        logger.info(f"MCP_SERVER_MODE: {self.MCP_SERVER_MODE}")
        logger.info(f"MCP_SERVER_URL: {self.MCP_SERVER_URL}")
        logger.info(f"LANGFUSE_HOST: {self.LANGFUSE_HOST}")
        logger.info(f"LANGFUSE_PUBLIC_KEY present: {'Yes' if self.LANGFUSE_PUBLIC_KEY else 'No'}")
        logger.info(f"LANGFUSE_SECRET_KEY present: {'Yes' if self.LANGFUSE_SECRET_KEY else 'No'}")
        logger.info(f"OTEL_EXPORTER_OTLP_ENDPOINT: {os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'Not set')}")
        logger.info(f"LOGFIRE_SERVICE_NAME: {self.LOGFIRE_SERVICE_NAME}")
        logger.info(f"LOGFIRE_SEND_TO_LOGFIRE: {self.LOGFIRE_SEND_TO_LOGFIRE}")
        logger.info(f"DEBUG: {self.DEBUG}")
        logger.info(f"ENVIRONMENT: {self.ENVIRONMENT}")
    
    def reload(self):
        """Reload configuration from environment variables."""
        if self.ENV_FILE.exists():
            load_dotenv(str(self.ENV_FILE), override=True)
        self._load_config()
        self._log_config()
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a configuration value by key."""
        return getattr(self, key, default)
    
    def validate(self) -> bool:
        """Validate that all required configuration values are present."""
        required_vars = [
            "OPENAI_API_KEY",
            "DATABASE_URL"
        ]
        
        missing_vars = [var for var in required_vars if not getattr(self, var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        return True

    def get_langfuse(self):
        """Get the Langfuse client instance."""
        return self.langfuse
    
    def _get_default_db_folder(self) -> str:
        """Get default database folder from config."""
        return self.DB_FOLDER

    def get_db_path(self, filename: str) -> str:
        """Get full path for a database file."""
        return os.path.join(self.DB_FOLDER, filename)

    def get_schema_path(self, filename: str) -> str:
        """Get full path for a schema file."""
        schemas_dir = os.path.join(self.DB_FOLDER, "schemas")
        Path(schemas_dir).mkdir(parents=True, exist_ok=True)
        return os.path.join(schemas_dir, filename)

    def get_export_path(self, folder_name: str) -> str:
        """Get full path for export folder."""
        export_dir = os.path.join(self.DB_FOLDER, "exports", folder_name)
        Path(export_dir).mkdir(parents=True, exist_ok=True)
        return export_dir

    def get_log_path(self, filename: str) -> str:
        """Get full path for log file."""
        logs_dir = os.path.join(self.DB_FOLDER, "logs")
        Path(logs_dir).mkdir(parents=True, exist_ok=True)
        return os.path.join(logs_dir, filename)

# Create a singleton instance
config = Config() 