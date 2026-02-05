from pydantic import BaseModel


class NotFoundRes(BaseModel):
    detail: str