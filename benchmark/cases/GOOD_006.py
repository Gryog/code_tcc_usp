from fastapi import APIRouter, status, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/v1", tags=["auth"])

class LoginCtx(BaseModel):
    username: str
    password: str

@router.post("/login", status_code=status.HTTP_200_OK)
async def login(creds: LoginCtx):
    # Faz login
    return {"token": "abc"}