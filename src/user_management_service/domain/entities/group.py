from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Group:
    id: Optional[int]
    name: str
    created_at: Optional[datetime]
