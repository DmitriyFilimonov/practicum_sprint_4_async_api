
from pydantic import BaseModel
from typing import Optional


class Film(BaseModel):
    id: str
    title: str
    description: Optional[str]