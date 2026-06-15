from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Local Override
    use_local_mock: bool = False

    # Database
    database_url: str
    redis_url: str = 'redis://redis:6379/0'

    # Auth
    jwt_secret: str
    jwt_algorithm: str = 'HS256'
    jwt_expiry_minutes: int = 15

    # LLM — Groq (gsk_...) or xAI/Grok (xai_...)
    groq_api_key: str = ''
    groq_model: str = 'llama-3.3-70b-versatile'
    xai_model: str = 'grok-3-fast'
    azure_openai_key: str = ''
    azure_openai_endpoint: str = ''
    llm_timeout_secs: int = 10

    # Freshworks
    freshworks_domain: str = ''
    freshworks_api_key: str = ''

    # RAG
    confidence_threshold: float = 0.80
    rag_top_k: int = 3
    session_timeout_minutes: int = 5

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'ignore'

settings = Settings()
