from uuid import UUID, uuid4
from datetime import datetime
from pydantic import EmailStr
from sqlmodel import SQLModel, Field, BigInteger, JSON


# Пользователь
class User(SQLModel, table=True):
    uuid: UUID = Field(default_factory=uuid4, primary_key=True)
    telegram_id: int = Field(sa_type=BigInteger, unique=True, index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)


class UserResume(SQLModel, table=True):
    uuid: UUID = Field(default_factory=uuid4, primary_key=True)
    user_uuid: UUID = Field(foreign_key='user.uuid', index=True, unique=True)

    text: str  # ← только текст резюме (из PDF)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class UserSearchFilter(SQLModel, table=True):
    uuid: UUID = Field(default_factory=uuid4, primary_key=True)
    user_uuid: UUID = Field(foreign_key='user.uuid', index=True, unique=True)

    text_query: str = Field(default='python')
    experience: list[str] = Field(
        sa_type=JSON,
        default=['between1And3', 'between3And6']
    )
    employment: list[str] = Field(
        sa_type=JSON,
        default=['full']
    )
    area_id: int = Field(default=113)  # Россия
    only_with_salary: bool = Field(default=False)
    min_match_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


# HeadHunter
class HHVacancy(SQLModel, table=True):
    id: str = Field(primary_key=True)
    title: str
    company: str
    url: str
    experience: str
    employment: str
    salary_from: int | None = None
    salary_to: int | None = None
    currency: str | None = None
    description: str
    key_skills: list[str] = Field(sa_type=JSON, default=[])
    published_at: str
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    updated_at: datetime = Field(default_factory=datetime.now)


class SentVacancyLog(SQLModel, table=True):
    user_uuid: UUID = Field(foreign_key='user.uuid', primary_key=True)
    vacancy_id: str = Field(foreign_key='hhvacancy.id', primary_key=True)
    sent_at: datetime = Field(default_factory=datetime.now)


# Рассылка по email
class BaseContact(SQLModel):
    uuid: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(max_length=255, index=True)
    company_name: str = Field(max_length=255, index=True)
    source_url: str = Field(max_length=500)
    parsed_at: datetime = Field(default_factory=datetime.now)
    outreach_status: str | None = Field(default=None, max_length=20)
    letter: str | None = Field(default=None, max_length=1000)
    sent_at: datetime | None = Field(default=None, nullable=True)


class ActiveContact(BaseContact, table=True):
    pass


class DeletedContact(BaseContact, table=True):
    deleted_at: datetime = Field(default_factory=datetime.now)