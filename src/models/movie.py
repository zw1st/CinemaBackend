from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    rating: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    release_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    duration: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )

    age_rating: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    poster_image_url: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    genres: Mapped[str | None] = mapped_column(Text)
    actors: Mapped[str | None] = mapped_column(Text)
    director: Mapped[str | None] = mapped_column(Text)
