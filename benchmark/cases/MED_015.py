from fastapi import APIRouter

router = APIRouter()

@router.post("/submit")
async def submit(data: dict):
    return {"received": True}