from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.local", env_file_encoding="utf-8")

    DB_URL: str

    # SMTP server config
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USERNAME: str
    SMTP_PASSWORD: str

    CRYPTO_SECRET_KEY: bytes


settings = Settings(_env_file=".env.local", _env_file_encoding="utf-8")
