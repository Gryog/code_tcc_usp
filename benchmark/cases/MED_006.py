from fastapi import APIRouter
import time

router = APIRouter()

@router.get("/sleep")
async def sleep_route():
    time.sleep(1) # Bloqueia o loop
    return {"status": "awake"}