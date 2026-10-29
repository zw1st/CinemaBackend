from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.user import User
from src.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from src.utils.auth_utils import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from src.utils.database import get_session

router = APIRouter(prefix="/auth", tags=["Authentication"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: RegisterRequest,
    session: SessionDep,
) -> AuthResponse:
    existing_user = session.scalar(
        select(User).where(User.email == data.email)
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    user = User(
        email=str(data.email),
        password_hash=hash_password(data.password),
        created_at=datetime.now(),
    )

    try:
        session.add(user)
        session.flush()

        access_token = create_access_token(user.id)
        raw_refresh_token, refresh_token_model = create_refresh_token(
            user.id
        )

        session.add(refresh_token_model)
        session.commit()
        session.refresh(user)

    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        ) from None

    return AuthResponse(
        access_token=access_token,
        refresh_token=raw_refresh_token,
        user=user,
    )


@router.post("/login", response_model=AuthResponse)
def login(
    data: LoginRequest,
    session: SessionDep,
) -> AuthResponse:
    user = session.scalar(
        select(User).where(User.email == data.email)
    )

    if user is None or not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(user.id)
    raw_refresh_token, refresh_token_model = create_refresh_token(
        user.id
    )

    session.add(refresh_token_model)
    session.commit()

    return AuthResponse(
        access_token=access_token,
        refresh_token=raw_refresh_token,
        user=user,
    )