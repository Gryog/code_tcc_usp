from fastapi import APIRouter, status

router = APIRouter(tags=["status"])

@router.get("/ping", status_code=status.HTTP_200_OK)
async def ping():
    '''Health check simples'''
    return {"ping": "pong"}