import uuid
from pydantic import BaseModel
from typing import Optional


class BoroughOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str]
    seo_title: Optional[str]
    seo_description: Optional[str]
    is_premium_area: bool
    escort_count: int = 0

    model_config = {"from_attributes": True}
