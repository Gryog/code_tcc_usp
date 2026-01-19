from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/api/v1", tags=["reports"])

@router.get(
    "/reports",
    response_model=List[ReportResponse],
    status_code=status.HTTP_200_OK,
    tags=["reports"]
)
async def get_reports(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[ReportResponse]:
    '''
    Lista relatórios com paginação.
    
    Returns:
        Lista de relatórios
    '''
    try:
        reports = db.query(Report).offset(skip).limit(limit).all()
        return reports
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro: {str(e)}"
        )