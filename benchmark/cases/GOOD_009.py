from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["items"])

class Item(BaseModel):
    name: str

@router.post("/items")
async def create_item(item: Item):
    '''Cria item'''
    return item