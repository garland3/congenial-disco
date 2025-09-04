from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    model_name: str = "openai/gpt-3.5-turbo"
    database_url: str = "sqlite:///./interview_app.db"
    
    class Config:
        env_file = ".env"

settings = Settings()