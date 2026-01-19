from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1", tags=["orders"])

@router.put(
    "/orders/{order_id}",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    tags=["orders"]
)
async def update_order(
    order_id: int = Path(..., gt=0, description="ID do pedido"),
    order_update: OrderUpdate = ...,
    db: Session = Depends(get_db)
) -> OrderResponse:
    '''
    Atualiza dados de um pedido existente.
    
    Args:
        order_id: ID do pedido a atualizar
        order_update: Dados atualizados do pedido
        db: Sessão do banco de dados
    
    Returns:
        Pedido atualizado
    
    Raises:
        HTTPException: Erro 404 se pedido não encontrado
        HTTPException: Erro 500 em caso de erro no banco
    '''
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pedido {order_id} não encontrado"
            )
        
        for key, value in order_update.dict(exclude_unset=True).items():
            setattr(order, key, value)
        
        db.commit()
        db.refresh(order)
        return order
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar pedido: {str(e)}"
        )