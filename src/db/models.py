from uuid import UUID, uuid4
from datetime import datetime
from pydantic import EmailStr
from sqlmodel import SQLModel, Field, BigInteger, JSON


# Пользователь
class User(SQLModel, table=True):
    uuid: UUID = Field(default_factory=uuid4, primary_key=True)
    telegram_id: int = Field(sa_type=BigInteger, unique=True, index=True)
    email: EmailStr | None = Field(default=None, unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = Field(default=True)


# HeadHunter
class HHProfile(SQLModel, table=True):
    uuid: UUID = Field(default_factory=uuid4, primary_key=True)

    user_uuid: UUID = Field(foreign_key='user.uuid', index=True)

    hh_access_token: str
    hh_refresh_token: str | None = None
    expires_at: datetime | None = None

    resume_id: str

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class HHSearchFilter(SQLModel, table=True):
    uuid: UUID = Field(default_factory=uuid4, primary_key=True)
    hh_profile_uuid: UUID = Field(foreign_key='hhprofile.uuid', index=True)

    # Основной текстовый запрос
    text_query: str

    # Опыт: значения из HH API: noExperience, between1And3, between3And6, moreThan6
    experience: list = Field(sa_type=JSON, default=['between1And3', 'between3And6'])

    # Занятость: full, part, project, volunteer, probation
    employment: list = Field(sa_type=JSON, default=['full'])

    # Регион (area_id в HH)
    area_id: int

    # Только с зарплатой?
    only_with_salary: bool = Field(default=False)

    # Минимальный порог соответствия (0.0 – 1.0)
    min_match_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class HHVacancy(SQLModel, table=True):
    id: str = Field(primary_key=True)  # vacancy_id на HH

    title: str
    employer_name: str
    url: str
    experience: str
    employment: str
    salary_from: int | None = None
    salary_to: int | None = None
    currency: str | None = None
    description: str
    key_skills: list = Field(sa_type=JSON, default=[])

    created_at: datetime = Field(default_factory=datetime.now, index=True)
    updated_at: datetime = Field(default_factory=datetime.now)


class HHApplicationLog(SQLModel, table=True):
    uuid: UUID = Field(default_factory=uuid4, primary_key=True)

    hh_profile_uuid: UUID = Field(foreign_key='hhprofile.uuid', index=True)
    hh_vacancy_id: str = Field(foreign_key='hhvacancy.id', index=True)

    match_score: float

    status: str = Field(default='pending', index=True)  # sent, error
    error_message: str | None = None

    letter: str | None = Field(default=None, max_length=1000)  # Сопроводительное письмо
    applied_at: datetime = Field(default_factory=datetime.now, index=True)


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