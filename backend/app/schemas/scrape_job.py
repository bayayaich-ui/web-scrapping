from datetime import datetime
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator

from app.models.scrape_job import JobStatus


class ScrapeJobCreate(BaseModel):
    url: AnyHttpUrl

    @field_validator("url")
    @classmethod
    def validate_http_url(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        if value.scheme not in {"http", "https"}:
            raise ValueError("Only HTTP and HTTPS URLs are supported")
        return value


class ScrapeJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    input_url: str
    status: JobStatus
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime


class ScrapeAcceptedResponse(BaseModel):
    job_id: UUID
    status: JobStatus
