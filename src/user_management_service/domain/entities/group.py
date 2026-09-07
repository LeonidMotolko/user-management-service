from datetime import datetime

from pydantic import BaseModel


class Group(BaseModel):
    id: int | None = None
    name: str
    created_at: datetime | None = None
