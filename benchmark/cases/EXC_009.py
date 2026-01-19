from fastapi import APIRouter, status, Depends
from sqlalchemy.sql import text

router = APIRouter(tags=["health"])

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    tags=["health"],
    response_model=dict
)
async def health_check(db: Session = Depends(get_db)) -> dict:
    '''
    Verifica a saúde da aplicação e conexão com banco.
    '''
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception:
        return {"status": "unhealthy", "database": "disconnected"}