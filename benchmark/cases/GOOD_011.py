from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["calc"])

@router.get("/divide")
async def divide(a: int, b: int):
    '''Faz divisão'''
    if b == 0:
        raise HTTPException(status_code=400, detail="Zero division")
    return {"result": a / b}