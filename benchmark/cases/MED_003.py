from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

router = APIRouter(tags=["invoices"])

@router.get(
    "/invoices/{invoice_id}",
    response_model=InvoiceResponse,
    status_code=status.HTTP_200_OK
)
async def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db)
) -> InvoiceResponse:
    '''Busca fatura por ID'''
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    return invoice