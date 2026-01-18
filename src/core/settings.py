import sys
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.utils.resume_loader import load_resume_text


class Settings(BaseSettings):
    # Метаданные приложения
    app_name: str = 'AutoApplyAI'
    debug: bool

    # Пути к резюме
    resume_pdf_path: Path = Field(default=Path('./resume/resume.pdf'))

    # Email (SMTP)
    email_host: str
    email_port: int
    email_user: str
    email_password: str

    # Config
    max_emails_per_24h: int

    # Redis
    redis_url: str

    # DataBase
    database_url: str

    # LLM
    llm_model: str
    llm_url: str

    embedding_model: str

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',  # игнорировать лишние переменные в .env
        case_sensitive=False  # EMAIL_USER == email_user
    )

    def __init__(self, **data):
        super().__init__(**data)
        try:
            self._resume_text = load_resume_text(self.resume_pdf_path)
        except Exception as e:
            print(f'❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось загрузить резюме из {self.resume_pdf_path}', file=sys.stderr)
            print(f'Причина: {e}', file=sys.stderr)
            sys.exit(1)

    @property
    def resume_text(self) -> str:
        return self._resume_text


# Экземпляр настроек
settings = Settings()