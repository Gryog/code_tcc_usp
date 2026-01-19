from fastapi import APIRouter
from typing import List

router = APIRouter(tags=["tags"])

@router.get("/tags", response_model=List[str])
async def get_tags():
    '''Lista todas as tags'''
    return ["tag1", "tag2"]