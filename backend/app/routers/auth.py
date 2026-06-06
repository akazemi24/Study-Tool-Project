import uuid
import httpx
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User
from app.services.auth_service import create_access_token, verify_token
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


class GoogleAuthRequest(BaseModel):
    code: str
    redirect_uri: str


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@router.post("/google")
async def google_auth(request: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": request.code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": request.redirect_uri,
                "grant_type": "authorization_code"
            }
        )

    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange code with Google")

    token_data = token_response.json()
    access_token = token_data.get("access_token")

    async with httpx.AsyncClient() as client:
        profile_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )

    if profile_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get user profile from Google")

    profile = profile_response.json()
    google_id = profile.get("id")
    email = profile.get("email")
    name = profile.get("name")
    avatar_url = profile.get("picture")

    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if not user:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=email,
            name=name,
            google_id=google_id,
            avatar_url=avatar_url
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        user.google_id = google_id
        user.avatar_url = avatar_url
        await db.commit()
        await db.refresh(user)

    jwt_token = create_access_token(str(user.id), user.email)

    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "avatar_url": user.avatar_url
        }
    }


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "avatar_url": current_user.avatar_url
    }