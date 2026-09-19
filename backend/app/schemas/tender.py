from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class TenderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    source_url: HttpUrl
    title: str | None = None
    description: str | None = None
    owner: str | None = None
    contact: str | None = None
    published_date: date | None = None
    deadline: date | None = None
    documents: list[HttpUrl] = Field(default_factory=list)
    extraction_method: str
    scraped_at: datetime


class TenderListResponse(BaseModel):
    items: list[TenderResponse]
    total: int
    page: int
    page_size: int
