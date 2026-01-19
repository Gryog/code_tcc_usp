from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/risky")
async def risky_op():
    try:
        # op
        pass
    except Exception:
        raise HTTPException(status_code=500, detail="Error")