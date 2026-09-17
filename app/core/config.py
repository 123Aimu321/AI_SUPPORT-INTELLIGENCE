from pathlib import Path

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):

    app_name: str = "AI Support Intelligence"

    app_version: str = "1.0.0"

    database_url: str = (
        f"sqlite:///{BASE_DIR / 'database' / 'support_tickets.db'}"
    )

    csv_path: str = str(
        BASE_DIR / "data" / "support_tickets.csv"
    )

    groq_api_key: str

    groq_model: str = "openai/gpt-oss-20b"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()