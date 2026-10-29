from fastapi import APIRouter, Depends

from src.models.user import User
from src.schemas.user import UserResponse
from src.utils.auth_dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user
