from fastapi import APIRouter

router = APIRouter()

@router.get("/data")
async def get_data():
    return {"a": 1, "b": 2, "c": [1,2,3]}