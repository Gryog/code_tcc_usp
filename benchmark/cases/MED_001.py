from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1", tags=["customers"])

@router.get("/customers", status_code=200)
async def get_customers(db: Session = Depends(get_db)):
    '''Retorna lista de clientes'''
    try:
        customers = db.query(Customer).all()
        return customers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))