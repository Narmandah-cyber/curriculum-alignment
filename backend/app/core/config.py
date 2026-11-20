"""Тохиргоо: .env файл эсвэл орчны хувьсагчаас уншина (.env.example-ийг харна уу)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Уялдаа API"
    database_url: str = "postgresql+psycopg://uyaldaa:uyaldaa@localhost:5432/uyaldaa"
    secret_key: str = "change-me"            # ПРОДАКШНД ЗААВАЛ СОЛИНО
    access_token_minutes: int = 60 * 8
    cors_origins: list[str] = ["http://localhost:5173"]

    # Шинжилгээний анхны утгууд (settings хүснэгтэд хадгалагдсаныг давуу гэж үзнэ)
    embedding_model: str = "sentence-transformers/LaBSE"
    link_threshold: float = 0.5               # θ — тэмдэглэгээтэй өгөгдөл дээр сонгоно
    hybrid_lambda: float = 0.7                # λ — тэмдэглэгээтэй өгөгдөл дээр сонгоно
    min_skill_frequency: float = 0.1          # τ
    llm_enabled: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
