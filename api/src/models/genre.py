from pydantic import BaseModel
from typing import Optional


class Genre(BaseModel):
    id: str
    name: str
    description: Optional[str]
