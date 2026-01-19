from fastapi import APIRouter

router = APIRouter()

@router.get("/check/{id}")
async def check(id: int):
    if id < 0:
        return {"error": "Invalid ID"} # Retorna 200 OK com erro no body
    return {"id": id}