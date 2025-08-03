from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from models import User  # your SQLAlchemy user model
from database import get_async_session  # your session getter

router = APIRouter()

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"

class GoogleAuthRequest(BaseModel):
    token: str

@router.post("/api/auth/google")
async def google_auth(
    req: GoogleAuthRequest, 
    session: AsyncSession = Depends(get_async_session)
):
    # 1. Verify token with Google
    async with httpx.AsyncClient() as client:
        resp = await client.get(GOOGLE_TOKENINFO_URL, params={"id_token": req.token})
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Google token")
    token_info = resp.json()
    email = token_info.get("email")
    name = token_info.get("name", "")
    google_id = token_info.get("sub")
    if not email or not google_id:
        raise HTTPException(status_code=400, detail="Google token missing email or user id")

    # 2. Upsert user in DB
    result = await session.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(email=email, name=name, google_id=google_id)
        session.add(user)
    else:
        user.email = email
        user.name = name
    await session.commit()

    # 3. (Optional) Issue your own JWT token here and return it
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "google_id": user.google_id,
        # "token": your_app_jwt_token
    }
