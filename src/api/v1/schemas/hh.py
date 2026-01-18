from pydantic import BaseModel, Field


class Salary(BaseModel):
    from_: int | None = Field(None, alias='from')
    to: int | None = None
    currency: str | None = None
    gross: bool | None = None

    class Config:
        populate_by_name = True


class HHVacancyMatchResult(BaseModel):
    vacancy_id: str
    title: str
    company: str
    url: str
    match_score: float
    salary: Salary | None
    published_at: str
    snippet: str


class HHSearchResponse(BaseModel):
    results: list[HHVacancyMatchResult]