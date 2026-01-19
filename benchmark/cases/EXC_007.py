from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["items"])

class ItemFilter(BaseModel):
    q: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None

async def parse_filter(
    q: Optional[str] = Query(None, description="Termo de busca"),
    min_price: Optional[float] = Query(None, ge=0, description="Preço mínimo"),
    max_price: Optional[float] = Query(None, ge=0, description="Preço máximo")
) -> ItemFilter:
    return ItemFilter(q=q, min_price=min_price, max_price=max_price)

@router.get(
    "/search",
    response_model=List[ItemResponse],
    tags=["items"]
)
async def search_items(
    filters: ItemFilter = Depends(parse_filter),
    db: Session = Depends(get_db)
) -> List[ItemResponse]:
    '''
    Busca itens com filtros complexos.
    '''
    query = db.query(Item)
    if filters.q:
        query = query.filter(Item.name.contains(filters.q))
    if filters.min_price:
        query = query.filter(Item.price >= filters.min_price)
    return query.all()