from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1")

@router.get(
    "/items",
    response_model=List[ItemResponse],
    status_code=status.HTTP_200_OK
)
async def get_items(
    db: Session = Depends(get_db)
) -> List[ItemResponse]:
    '''Recupera lista de items'''
    try:
        items = db.query(Item).all()
        return items
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )