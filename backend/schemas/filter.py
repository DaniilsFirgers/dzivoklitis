from pydantic import BaseModel, Field
from pydantic import BaseModel, Field, field_validator


class FilterCreate(BaseModel):
    """Schema for creating a new filter"""
    name: str
    city: str
    district: str
    rooms_range: list[int] = Field(..., min_items=2, max_items=2)
    price_range: list[int] = Field(..., min_items=2, max_items=2)
    area_range: list[int] = Field(..., min_items=2, max_items=2)
    floor_range: list[int] = Field(..., min_items=2, max_items=2)
    tg_user_id: int

    @field_validator("rooms_range", "price_range", "area_range", "floor_range")
    def validate_ranges(cls, value):
        if value[0] > value[1]:
            raise ValueError(
                "First value must be less than or equal to second value")
        return value


class FilterResponse(BaseModel):
    """Schema for returning filter data"""
    id: int
    name: str
    city: str
    district: str
    rooms_range: list[int] = Field(..., min_items=2, max_items=2)
    price_range: list[int] = Field(..., min_items=2, max_items=2)
    area_range: list[int] = Field(..., min_items=2, max_items=2)
    floor_range: list[int] = Field(..., min_items=2, max_items=2)

    class Config:
        orm_mode = True  # Pydantic ORM mode to work with SQLAlchemy models
