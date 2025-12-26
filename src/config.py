from typing import Literal

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", case_sensitive=False)

    application_name: str = "License Service"
    environment: Literal["development", "testing", "production"] = "development"
    debug: bool = True
    log_level: str = "INFO"

    database_url: str = "sqlite:///./test.db"
    database_echo: bool = False

    api_version: str = "v1"
    api_prefix: str = "/api"

    server_port: int = 8000


settings = Settings()
