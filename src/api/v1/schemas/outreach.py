from datetime import datetime
from pydantic import BaseModel


class SendOutreachResponse(BaseModel):
    '''Ответ на запрос запуска рассылки.'''
    status: str  # 'started' | 'limit_exceeded'
    message: str
    sent_count: int | None = None
    max_allowed: int | None = None


class StatusOutreachResponse(BaseModel):
    '''Текущее состояние рассылки.'''
    is_running: bool
    started_at: datetime | None = None
    sent_count: int
    max_allowed: int
    recently_sent_to: dict


class GenerateLetterRequest(BaseModel):
    '''Запрос на генерацию сопроводительного письма.'''
    company_name: str


class GenerateLetterResponse(BaseModel):
    '''Ответ с сгенерированным письмом.'''
    letter: str
