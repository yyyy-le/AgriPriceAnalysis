from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DEEPSEEK_API_KEY: str = ''
    DEEPSEEK_BASE_URL: str = 'https://api.deepseek.com'
    DEEPSEEK_MODEL: str = 'deepseek-chat'

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

settings = Settings()