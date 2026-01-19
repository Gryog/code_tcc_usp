from fastapi import APIRouter, status
from typing import Dict

router = APIRouter(tags=["misc"])

@router.get("/config", response_model=Dict, status_code=status.HTTP_200_OK)
async def get_config() -> Dict:
    '''Retorna configurações'''
    return {"version": "1.0", "env": "prod"}