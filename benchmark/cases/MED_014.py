from fastapi import APIRouter

router = APIRouter()
COUNTER = 0

@router.get("/count")
async def get_count():
    global COUNTER
    COUNTER += 1
    return {"count": COUNTER}