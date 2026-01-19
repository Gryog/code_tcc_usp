from fastapi import APIRouter

router = APIRouter()

@router.get("/filter")
async def filter_items(where: str):
    # Recebe cláusula raw, perigoso
    return {"query": f"SELECT * FROM items WHERE {where}"}