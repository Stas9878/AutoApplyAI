from pydantic import BaseModel, Field, field_validator

from src.platforms.hh.constants import HH_EXPERIENCE_OPTIONS, HH_EMPLOYMENT_OPTIONS


class Salary(BaseModel):
    from_: int | None = Field(None, alias='from')
    to: int | None = None
    currency: str | None = None
    gross: bool | None = None

    class Config:
        populate_by_name = True


class HHVacancyMatchResult(BaseModel):
    id: str
    title: str
    company: str
    url: str
    match_score: float
    salary_from: int | None = None
    salary_to: int | None = None
    currency: str | None = None
    published_at: str
    snippet: str



class HHSearchResponse(BaseModel):
    results: list[HHVacancyMatchResult]


class UserSearchFilterUpdate(BaseModel):
    text_query: str
    experience: list[str] = ['between1And3', 'between3And6']
    employment: list[str] = ['full']
    area_id: int = 113
    only_with_salary: bool = False
    min_match_threshold: float = 0.7

    @field_validator('experience')
    def validate_experience(cls, v):
        for item in v:
            if item not in HH_EXPERIENCE_OPTIONS:
                raise ValueError(f'Недопустимое значение опыта: {item}')
        return v

    @field_validator('employment')
    def validate_employment(cls, v):
        for item in v:
            if item not in HH_EMPLOYMENT_OPTIONS:
                raise ValueError(f'Недопустимый тип занятости: {item}')
        return v

    @field_validator('min_match_threshold')
    def validate_threshold(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError('Порог должен быть от 0.0 до 1.0')
        return v