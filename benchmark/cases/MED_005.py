from fastapi import APIRouter

router = APIRouter()

@router.get("/calc")
async def calculate(x, y):
    return {"sum": int(x) + int(y)}