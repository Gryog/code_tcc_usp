from fastapi import APIRouter, status

router = APIRouter(tags=["test"])

@router.get("/debug", status_code=status.HTTP_200_OK)
async def debug_endpoint():
    '''Endpoint para debug'''
    print("Debug endpoint called")
    return {"status": "ok"}