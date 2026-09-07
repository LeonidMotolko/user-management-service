from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Group(BaseModel):
    id: Optional[int] = None
    name: str
    created_at: Optional[datetime] = None
