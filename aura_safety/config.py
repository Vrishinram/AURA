"""
Configuration management for AI Safety Red Team Agent using Pydantic Settings.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Gemini
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    default_gemini_model: str = Field(default="gemini-2.5-flash", alias="DEFAULT_GEMINI_MODEL")

    # OpenAI / Compatible
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: Optional[str] = Field(default=None, alias="OPENAI_BASE_URL")
    default_openai_model: str = Field(default="gpt-4o-mini", alias="DEFAULT_OPENAI_MODEL")

    # Judge / Evaluator
    evaluator_provider: str = Field(default="heuristic", alias="EVALUATOR_PROVIDER")
    evaluator_model: Optional[str] = Field(default="gemini-2.5-flash", alias="EVALUATOR_MODEL")

    # General & Storage
    runs_dir: Path = Field(default=Path("data/runs"), alias="RUNS_DIR")
    timeout_seconds: int = Field(default=30, alias="TIMEOUT_SECONDS")
    max_retries: int = Field(default=3, alias="MAX_RETRIES")
    temperature: float = Field(default=0.0, alias="TEMPERATURE")


def get_settings() -> Settings:
    """Return a cached or newly initialized Settings instance."""
    return Settings()
