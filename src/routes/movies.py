from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.movie import Movie
from src.models.user import User
from src.schemas.movie import MovieCreate, MovieResponse
from src.utils.auth_dependencies import get_current_user
from src.utils.database import get_session

SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[User, Depends(get_current_user)]

router = APIRouter(
    prefix="/movies", tags=["Movies"], dependencies=[Depends(get_current_user)]
)


@router.get("", response_model=list[MovieResponse])
def get_movies(
    session: SessionDep,
    title: Annotated[str | None, Query()] = None,
) -> list[Movie]:
    query = select(Movie)

    title = title.strip() if title else None

    if title:
        query = query.where(Movie.title.ilike(f"%{title}%"))

    return list(session.scalars(query.order_by(Movie.title)).all())


@router.get("/{movie_id}", response_model=MovieResponse)
def get_movie(movie_id: int, session: SessionDep) -> Movie:
    movie = session.get(Movie, movie_id)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )

    return movie


@router.post(
    "",
    response_model=MovieResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_movie(
    data: MovieCreate,
    session: SessionDep,
) -> Movie:
    movie = Movie(
        title=data.title,
        rating=data.rating,
        is_active=True,
        release_date=data.release_date,
        duration=data.duration,
        age_rating=data.age_rating,
        poster_image_url=(
            str(data.poster_image_url) if data.poster_image_url is not None else None
        ),
        description=data.description,
        genres=data.genres,
        actors=data.actors,
        director=data.director,
    )

    session.add(movie)

    try:
        session.commit()
        session.refresh(movie)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A movie with this title already exists",
        ) from None

    return movie


@router.delete(
    "/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_movie(movie_id: int, session: SessionDep) -> Response:
    movie = session.get(Movie, movie_id)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )

    session.delete(movie)
    session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{movie_id}/deactivate", response_model=MovieResponse)
def deactivate_movie(movie_id: int, session: SessionDep) -> Movie:
    movie = session.get(Movie, movie_id)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )

    movie.is_active = False
    session.commit()
    session.refresh(movie)

    return movie


@router.patch("/{movie_id}/restore", response_model=MovieResponse)
def restore_movie(movie_id: int, session: SessionDep) -> Movie:
    movie = session.get(Movie, movie_id)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )

    movie.is_active = True
    session.commit()
    session.refresh(movie)

    return movie
