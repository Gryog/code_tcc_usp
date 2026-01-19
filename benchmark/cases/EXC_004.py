from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1", tags=["categories"])

@router.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["categories"]
)
async def delete_category(
    category_id: int = Path(..., gt=0, description="ID da categoria"),
    db: Session = Depends(get_db)
) -> None:
    '''
    Remove uma categoria (soft delete).
    
    Args:
        category_id: ID da categoria a remover
        db: Sessão do banco de dados
    
    Raises:
        HTTPException: Erro 404 se categoria não encontrada
        HTTPException: Erro 500 em caso de erro no banco
    '''
    try:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Categoria {category_id} não encontrada"
            )
        
        category.deleted_at = datetime.utcnow()
        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao deletar categoria: {str(e)}"
        )