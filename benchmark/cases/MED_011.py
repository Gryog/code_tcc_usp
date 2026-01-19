from fastapi import APIRouter

router = APIRouter()

@router.get("/getUserInfo")
async def get_user_info():
    return {"user": "info"}