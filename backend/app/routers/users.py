import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.models.user import User as UserModel
from app.repositories.user_repo import UserRepository
from app.schemas.user import User, UserCreateRequest, UserListResponse, UserUpdateRequest
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserListResponse)
def list_users(
    _: Annotated[UserModel, Depends(require_permission("users:read"))],
    db: Session = Depends(get_db),
):
    items = user_service.list_users(UserRepository(db))
    return UserListResponse(items=items, total=len(items))


@router.post("", response_model=User, status_code=201)
def create_user(
    body: UserCreateRequest,
    _: Annotated[UserModel, Depends(require_permission("users:write"))],
    db: Session = Depends(get_db),
):
    return user_service.create_user(body, UserRepository(db))


@router.get("/{user_id}", response_model=User)
def get_user(
    user_id: uuid.UUID,
    _: Annotated[UserModel, Depends(require_permission("users:read"))],
    db: Session = Depends(get_db),
):
    return user_service.get_user_or_404(user_id, UserRepository(db))


@router.put("/{user_id}", response_model=User)
def update_user(
    user_id: uuid.UUID,
    body: UserUpdateRequest,
    _: Annotated[UserModel, Depends(require_permission("users:write"))],
    db: Session = Depends(get_db),
):
    repo = UserRepository(db)
    user = user_service.get_user_or_404(user_id, repo)
    return user_service.update_user(user, body, repo)


@router.delete("/{user_id}", response_model=User)
def deactivate_user(
    user_id: uuid.UUID,
    current_user: Annotated[UserModel, Depends(require_permission("users:write"))],
    db: Session = Depends(get_db),
):
    repo = UserRepository(db)
    user = user_service.get_user_or_404(user_id, repo)
    return user_service.deactivate_user(user, current_user, repo)
