from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from fastapi import FastAPI
from api.auth import router as auth_router

app = FastAPI()
app.include_router(auth_router)


# Enable CORS for your frontend (adjust origins as needed!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev, use "*" (all). For prod, restrict to your frontend URL.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"

class GoogleAuthRequest(BaseModel):
    token: str

@app.post("/api/auth/google")
async def google_auth(req: GoogleAuthRequest):
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

    # 2. Here you would insert/find the user in your DB.
    # For demo, just return the info.
    return {
        "email": email,
        "name": name,
        "google_id": google_id,
    }
