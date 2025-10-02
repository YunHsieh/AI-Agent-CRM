from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    # Existing settings
    DEBUG: str = os.getenv("DEBUG", "")
    # POSTGRES_URI: str = os.getenv('POSTGRES_URI')
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY').strip()

    OTEL_EXPORTER_OTLP_ENDPOINT: str = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    OTEL_SERVICE_NAME: str = os.getenv("OTEL_SERVICE_NAME", "")
    AGENT_URL: str = os.getenv("AGENT_URL", "")
    MILVUS_URI: str = os.getenv("MILVUS_URI", "")
    TOKENIZERS_PARALLELISM: bool = os.getenv("TOKENIZERS_PARALLELISM", False)

    model_config = ConfigDict(
        env_file=".env"
    )


SETTINGS = Settings()
