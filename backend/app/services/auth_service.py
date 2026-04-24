from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    is_refresh_token_revoked,
    revoke_refresh_token,
    verify_password,
)
from app.repositories.user_repo import UserRepository
from app.schemas.auth import AccessTokenResponse, TokenResponse


def login(email: str, password: str, db: Session) -> TokenResponse:
    repo = UserRepository(db)
    user = repo.get_by_email(email)
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"},
        )
    access_token = create_access_token(user.id, user.role.value)
    refresh_token = create_refresh_token(user.id)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


def refresh(refresh_token: str, db: Session) -> AccessTokenResponse:
    if is_refresh_token_revoked(refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_REVOKED", "message": "Refresh token has been revoked"},
        )
    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Invalid or expired refresh token"},
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Not a refresh token"},
        )

    import uuid
    user_id = uuid.UUID(payload["sub"])
    repo = UserRepository(db)
    user = repo.get(user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    access_token = create_access_token(user.id, user.role.value)
    return AccessTokenResponse(access_token=access_token)


def logout(refresh_token: str) -> None:
    revoke_refresh_token(refresh_token)
