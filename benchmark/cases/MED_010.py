from fastapi import APIRouter

router = APIRouter()

@router.post("/process")
async def process_data(data: dict):
    # Lógica complexa aqui
    res = 0
    for k, v in data.items():
        if isinstance(v, int):
            res += v * 2
    return {"result": res}