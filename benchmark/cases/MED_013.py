from fastapi import APIRouter

router = APIRouter()

@router.get("/db-test")
async def db_test():
    conn = "sqlite:///db.sqlite" # Hardcoded
    return {"conn": conn}