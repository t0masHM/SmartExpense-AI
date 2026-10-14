from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_user: str = "capton"
    postgres_password: str = "capton_local_dev"
    postgres_db: str = "capton"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    secret_key: str = "cambia-esta-clave-en-produccion"
    access_token_expire_minutes: int = 720
    algorithm: str = "HS256"

    cors_origins: str = "http://localhost:8080,http://localhost:5173"
    upload_dir: str = "./uploads"
    model_dir: str = "./models"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
