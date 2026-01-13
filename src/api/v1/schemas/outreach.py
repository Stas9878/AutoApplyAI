from pydantic import BaseModel


class SendOutreachResponse(BaseModel):
    status: str  # 'started' | 'limit_exceeded'
    message: str
    sent_count: int | None = None
    max_allowed: int | None = None


class GenerateLetterRequest(BaseModel):
    company_name: str


class GenerateLetterResponse(BaseModel):
    letter: str