import uuid
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
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
    credential: str


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
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        
        idinfo = id_token.verify_oauth2_token(
            request.credential,
            google_requests.Request(),
            settings.google_client_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid token: {str(e)}")

    google_id = idinfo.get("sub")
    email = idinfo.get("email")
    name = idinfo.get("name")
    avatar_url = idinfo.get("picture")

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