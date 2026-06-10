"""CN: 用户默认骑行偏好 API，用于读取和保存前端设置页的个人画像。
EN: User profile API for loading and saving the default rider preferences used by the settings page.
"""

from fastapi import APIRouter, HTTPException, Request

from app.repositories.user_profile_repository import get_default_user_profile, save_default_user_profile
from app.schemas.ride_plan import UserProfilePayload


router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


@router.get("/default", response_model=UserProfilePayload)
async def get_default_profile(request: Request) -> UserProfilePayload:
    database_url = getattr(request.app.state, "database_url", None)
    if not database_url:
        raise HTTPException(status_code=500, detail="database-url-missing")
    profile = get_default_user_profile(database_url)
    if profile is None:
        return UserProfilePayload()
    return UserProfilePayload.model_validate(profile)


@router.put("/default", response_model=UserProfilePayload)
async def put_default_profile(payload: UserProfilePayload, request: Request) -> UserProfilePayload:
    database_url = getattr(request.app.state, "database_url", None)
    if not database_url:
        raise HTTPException(status_code=500, detail="database-url-missing")
    saved = save_default_user_profile(database_url, payload.model_dump())
    return UserProfilePayload.model_validate(saved)
