import uuid

from fastapi import HTTPException

from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreateRequest, UserUpdateRequest


def list_users(repo: UserRepository) -> list[User]:
    return repo.list_all()


def get_user_or_404(user_id: uuid.UUID, repo: UserRepository) -> User:
    user = repo.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def create_user(data: UserCreateRequest, repo: UserRepository) -> User:
    if repo.get_by_email_any(data.email):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        id=uuid.uuid4(),
        email=data.email,
        full_name=data.full_name,
        role=data.role,
        password_hash=hash_password(data.password),
        is_active=True,
    )
    return repo.save(user)


def update_user(user: User, data: UserUpdateRequest, repo: UserRepository) -> User:
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.password is not None:
        user.password_hash = hash_password(data.password)
    return repo.save(user)


def deactivate_user(user: User, current_user: User, repo: UserRepository) -> User:
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    return repo.deactivate(user)
