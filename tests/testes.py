# ============================================================================
# EXEMPLOS DE CÓDIGO PARA TESTE
# ============================================================================

# Exemplo 1: CÓDIGO IDEAL (esperado: ~98/100)
EXAMPLE_1_IDEAL = """
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["users"])

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

@router.get(
    "/users",
    response_model=List[UserResponse],
    status_code=status.HTTP_200_OK,
    tags=["users"]
)
async def get_users(
    skip: int = Query(0, ge=0, description="Registros a pular"),
    limit: int = Query(100, ge=1, le=100, description="Limite de registros"),
    db: Session = Depends(get_db)
) -> List[UserResponse]:
    '''
    Recupera lista de usuários com paginação.
    
    Args:
        skip: Número de registros a pular
        limit: Limite de registros a retornar
        db: Sessão do banco de dados
    
    Returns:
        Lista de usuários
    
    Raises:
        HTTPException: Erro 500 se houver falha no banco
    '''
    try:
        users = db.query(User).offset(skip).limit(limit).all()
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar usuários: {str(e)}"
        )
"""

# Exemplo 2: CÓDIGO BOM (esperado: ~80/100)
EXAMPLE_2_GOOD = """
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/users", status_code=201)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    '''Cria um novo usuário'''
    try:
        new_user = User(**user.dict())
        db.add(new_user)
        db.commit()
        return new_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""

# Exemplo 3: CÓDIGO MÉDIO (esperado: ~58/100)
EXAMPLE_3_MEDIUM = """
from fastapi import FastAPI, Depends

app = FastAPI()

@app.get("/user/{user_id}")
def getUserById(user_id: int, db=Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    return user
"""

# Exemplo 4: CÓDIGO RUIM (esperado: ~31/100)
EXAMPLE_4_BAD = """
from fastapi import FastAPI

app = FastAPI()

@app.post("/users")
def create(data):
    u = User()
    u.name = data['name']
    u.email = data['email']
    db.add(u)
    db.commit()
    return {"msg": "ok"}
"""

# Exemplo 5: CÓDIGO MUITO RUIM (esperado: ~12/100)
EXAMPLE_5_VERY_BAD = """
@app.get("/users")
def get():
    return db.query(User).all()
"""

# Exemplo 6: PROBLEMAS DE NOMENCLATURA (esperado: ~65/100)
EXAMPLE_6_NAMING = """
from fastapi import APIRouter, status

router = APIRouter()

@router.delete("/users/{UserId}", status_code=204)
async def DeleteUserFunction(UserId: int, DataBase = Depends(get_db)):
    '''Remove usuário'''
    USER = DataBase.query(User).filter(User.id == UserId).first()
    if USER:
        DataBase.delete(USER)
        DataBase.commit()
    return None
"""

# Exemplo 7: SEM TRATAMENTO DE ERROS (esperado: ~54/100)
EXAMPLE_7_NO_ERROR_HANDLING = """
from fastapi import APIRouter, Depends, status
from typing import List

router = APIRouter()

@router.get(
    "/users/{user_id}/orders",
    response_model=List[OrderResponse],
    status_code=status.HTTP_200_OK,
    tags=["orders"]
)
async def get_user_orders(
    user_id: int,
    db: Session = Depends(get_db)
) -> List[OrderResponse]:
    '''Recupera pedidos de um usuário'''
    user = db.query(User).filter(User.id == user_id).first()
    orders = db.query(Order).filter(Order.user_id == user.id).all()
    return orders
"""

# Exemplo 8: ESTRUTURA DIFERENTE MAS VÁLIDA (esperado: ~95/100)
EXAMPLE_8_VALID_ALT = """
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

router = APIRouter(prefix="/api/v1", tags=["users"])

@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    tags=["users"]
)
async def update_user(
    user_id: int,
    user_update: UserCreate,
    db: Session = Depends(get_db)
) -> UserResponse:
    '''
    Atualiza usuário existente.
    
    Args:
        user_id: ID do usuário
        user_update: Dados atualizados
        db: Sessão do banco
    
    Returns:
        Usuário atualizado
    '''
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        for key, value in user_update.dict().items():
            setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        return user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar: {str(e)}"
        )
"""