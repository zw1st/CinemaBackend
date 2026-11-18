from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.refresh_token import RefreshToken
from src.models.user import User
from src.schemas.auth import AuthResponse, LoginRequest, RefreshRequest, RegisterRequest
from src.utils.auth_utils import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    is_refresh_token_valid,
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
    existing_user = session.scalar(select(User).where(User.email == data.email))

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
        raw_refresh_token, refresh_token_model = create_refresh_token(user.id)

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
    user = session.scalar(select(User).where(User.email == data.email))

    if user is None or not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(user.id)
    raw_refresh_token, refresh_token_model = create_refresh_token(user.id)

    session.add(refresh_token_model)
    session.commit()

    return AuthResponse(
        access_token=access_token,
        refresh_token=raw_refresh_token,
        user=user,
    )


@router.post("/refresh", response_model=AuthResponse)
def refresh_tokens(
    data: RefreshRequest,
    db: Session = Depends(get_session),
):
    # 1. Хешируем полученный refresh-токен
    token_hash = hash_refresh_token(data.refresh_token)

    # 2. Ищем токен в БД и блокируем запись на время транзакции
    refresh_token = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .with_for_update()
    )

    # 3. Проверяем существование и действительность токена
    if refresh_token is None or not is_refresh_token_valid(refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # 4. Получаем пользователя
    user = db.get(User, refresh_token.user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # 5. Отзываем старый refresh-токен
    refresh_token.revoked = True

    # 6. Создаём новый refresh-токен
    new_refresh_token, new_refresh_token_model = create_refresh_token(user.id)

    db.add(new_refresh_token_model)

    # 7. Создаём новый access-токен
    new_access_token = create_access_token(user.id)

    # 8. Сохраняем изменения
    db.commit()

    return AuthResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        user=user,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    request: RefreshRequest,
    session: Session = Depends(get_session),
):
    token_hash = hash_refresh_token(request.refresh_token)

    refresh_token = session.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )

    if refresh_token and not refresh_token.revoked:
        refresh_token.revoked = True
        session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
