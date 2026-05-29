"""认证API

提供用户注册、登录、获取当前用户等接口。
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from db.database import get_db
from db.models import User

logger = structlog.get_logger()
router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── 请求/响应模型 ────────────────────────────────────────


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str | None = Field(None, max_length=100)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: str
    displayName: str | None = None
    avatarUrl: str | None = None
    isActive: bool
    createdAt: str


class UpdateProfileRequest(BaseModel):
    display_name: str | None = Field(None, max_length=100)
    avatar_url: str | None = None


# ── 路由 ────────────────────────────────────────────────


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """注册新用户"""
    # 检查用户名是否已存在
    existing = await db.execute(select(User).where(User.username == req.username))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名已被注册",
        )

    # 检查邮箱是否已存在
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="邮箱已被注册",
        )

    # 创建用户
    user = User(
        username=req.username,
        email=req.email,
        hashed_password=hash_password(req.password),
        display_name=req.display_name or req.username,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("user_registered", user_id=user.id, username=user.username)

    token = create_access_token({"sub": user.id, "username": user.username})
    return TokenResponse(
        access_token=token,
        user=_user_to_response(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
        )

    logger.info("user_logged_in", user_id=user.id, username=user.username)

    token = create_access_token({"sub": user.id, "username": user.username})
    return TokenResponse(
        access_token=token,
        user=_user_to_response(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return _user_to_response(current_user)


@router.put("/me", response_model=UserResponse)
async def update_me(
    req: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新当前用户信息"""
    if req.display_name is not None:
        current_user.display_name = req.display_name
    if req.avatar_url is not None:
        current_user.avatar_url = req.avatar_url

    await db.commit()
    await db.refresh(current_user)

    return _user_to_response(current_user)


# ── 辅助函数 ────────────────────────────────────────────


def _user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        displayName=user.display_name,
        avatarUrl=user.avatar_url,
        isActive=user.is_active,
        createdAt=user.created_at.isoformat() if user.created_at else "",
    )
