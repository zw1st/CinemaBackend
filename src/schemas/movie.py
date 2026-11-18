from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class MovieCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    rating: Decimal = Field(ge=0, le=10, max_digits=4, decimal_places=2)
    release_date: date
    duration: int = Field(gt=0, le=32767)
    age_rating: str = Field(min_length=1, max_length=10)

    poster_image_url: HttpUrl | None = None
    description: str | None = None
    genres: str | None = None
    actors: str | None = None
    director: str | None = None


class MovieResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    rating: Decimal
    is_active: bool
    release_date: date
    duration: int
    age_rating: str
    poster_image_url: str | None
    description: str | None
    genres: str | None
    actors: str | None
    director: str | None
