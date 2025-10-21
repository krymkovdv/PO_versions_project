from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TractorsSchema(BaseModel):
    model: str
    region: str
    owner_name: str
    assembly_date: datetime

    class Config:
        from_attributes = True  # ← позволяет читать из ORM-объекта