from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.models.user import User
from app.schemas.auth import AccessTokenResponse, LoginRequest, RefreshRequest, TokenResponse
from app.schemas.user import User as UserSchema
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    return auth_service.login(body.email, body.password, db)


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    return auth_service.refresh(body.refresh_token, db)


@router.post("/logout", status_code=204)
def logout(body: RefreshRequest):
    auth_service.logout(body.refresh_token)


@router.get("/me", response_model=UserSchema)
def me(current_user: Annotated[User, Depends(require_permission("equipment:read"))]):
    return current_user
