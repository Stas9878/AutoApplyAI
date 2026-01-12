from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone


class BaseContact(SQLModel):
    uuid: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(max_length=255, unique=True)
    company_name: str = Field(max_length=255)
    source_url: str = Field(max_length=500)
    parsed_at: datetime = Field(default_factory=datetime.now)


class ActiveContact(BaseContact, table=True):
    pass


class DeletedContact(BaseContact, table=True):
    deleted_at: datetime = Field(default_factory=datetime.now)