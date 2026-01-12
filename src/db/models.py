from uuid import UUID, uuid4
from datetime import datetime
from sqlmodel import SQLModel, Field


class BaseContact(SQLModel):
    uuid: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(max_length=255, index=True)
    company_name: str = Field(max_length=255, index=True)
    source_url: str = Field(max_length=500)
    parsed_at: datetime = Field(default_factory=datetime.now)
    outreach_status: str | None = Field(default=None, max_length=20)
    sent_at: datetime | None = Field(default=None, nullable=True)


class ActiveContact(BaseContact, table=True):
    pass


class DeletedContact(BaseContact, table=True):
    deleted_at: datetime = Field(default_factory=datetime.now)