from pydantic import BaseModel, Field


class SequenceJobCreate(BaseModel):
    sequence: str = Field(min_length=12)
    mode: str = "auto"
    query_name: str = "query"


class JobOut(BaseModel):
    id: str
    mode: str
    status: str
    engine: str = ""
    message: str = ""
    result_download_url: str | None = None
    hits: list[dict] = []
