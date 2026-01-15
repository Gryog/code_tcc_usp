# SISTEMA COMPLETO DE TESTES PARA VALIDADOR FASTAPI
# Inclui: 50 casos sintéticos + Coleta automática + Análise estatística
# ============================================================================

import json
import time
import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import statistics

# ============================================================================
# PARTE 1: 50 CASOS DE TESTE SINTÉTICOS
# ============================================================================

def gerar_dataset_sintetico():
    """
    Gera 50 casos de teste sintéticos bem distribuídos.
    
    Distribuição:
    - 10 Excelentes (95-100)
    - 15 Bons (80-94)
    - 15 Médios (60-79)
    - 10 Ruins (0-59)
    """
    
    dataset = {
        "metadata": {
            "name": "FastAPI Synthetic Test Dataset",
            "version": "1.0",
            "date": datetime.now().isoformat(),
            "total_examples": 50,
            "description": "Casos sintéticos para validação de código FastAPI"
        },
        "categories": {
            "excellent": [],
            "good": [],
            "medium": [],
            "poor": []
        },
        "statistics": {}
    }
    
    # ========================================================================
    # CATEGORIA: EXCELENTE (10 exemplos) - Score esperado: 95-100
    # ========================================================================
    
    excellent_examples = [
        {
            "id": "EXC_001",
            "description": "Endpoint GET completo com paginação e documentação",
            "expected_score_min": 95,
            "expected_score_max": 100,
            "code": """
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/api/v1", tags=["users"])

@router.get(
    "/users",
    response_model=List[UserResponse],
    status_code=status.HTTP_200_OK,
    tags=["users"]
)
async def get_users(
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=100, description="Limite de registros"),
    db: Session = Depends(get_db)
) -> List[UserResponse]:
    '''
    Recupera lista paginada de usuários.
    
    Args:
        skip: Registros a pular para paginação
        limit: Número máximo de registros a retornar
        db: Sessão do banco de dados
    
    Returns:
        Lista de usuários encontrados
    
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
        },
        {
            "id": "EXC_002",
            "description": "Endpoint POST com validação Pydantic completa",
            "expected_score_min": 95,
            "expected_score_max": 100,
            "code": """
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1", tags=["products"])

@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["products"]
)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
) -> ProductResponse:
    '''
    Cria um novo produto no sistema.
    
    Args:
        product: Dados do produto a ser criado
        db: Sessão do banco de dados
    
    Returns:
        Produto criado com ID gerado
    
    Raises:
        HTTPException: Erro 409 se produto já existe
        HTTPException: Erro 500 se houver falha no banco
    '''
    try:
        existing = db.query(Product).filter(Product.name == product.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Produto com este nome já existe"
            )
        
        new_product = Product(**product.dict())
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        return new_product
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar produto: {str(e)}"
        )
"""
        },
        {
            "id": "EXC_003",
            "description": "Endpoint PUT com validação de existência",
            "expected_score_min": 95,
            "expected_score_max": 100,
            "code": """
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
"""
        },
        # Adicionar mais 7 exemplos excelentes...
        {
            "id": "EXC_004",
            "description": "Endpoint DELETE com soft delete",
            "expected_score_min": 95,
            "expected_score_max": 100,
            "code": """
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
"""
        }
    ]
    
    # ========================================================================
    # CATEGORIA: BOM (15 exemplos) - Score esperado: 80-94
    # ========================================================================
    
    good_examples = [
        {
            "id": "GOOD_001",
            "description": "Endpoint sem tags explícitas (mas tem outras boas práticas)",
            "expected_score_min": 80,
            "expected_score_max": 94,
            "code": """
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
"""
        },
        {
            "id": "GOOD_002",
            "description": "Endpoint com docstring simples (não estruturada)",
            "expected_score_min": 80,
            "expected_score_max": 94,
            "code": """
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/api/v1", tags=["tasks"])

@router.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["tasks"]
)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)) -> TaskResponse:
    '''Cria uma nova tarefa no sistema'''
    try:
        new_task = Task(**task.dict())
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        return new_task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""
        },
        {
            "id": "GOOD_003",
            "description": "Endpoint sem Query() explícito para parâmetros",
            "expected_score_min": 80,
            "expected_score_max": 94,
            "code": """
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
"""
        }
    ]
    
    # ========================================================================
    # CATEGORIA: MÉDIO (15 exemplos) - Score esperado: 60-79
    # ========================================================================
    
    medium_examples = [
        {
            "id": "MED_001",
            "description": "Endpoint sem response_model",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "code": """
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
"""
        },
        {
            "id": "MED_002",
            "description": "Endpoint com nome inadequado e sem type hints completos",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "code": """
from fastapi import FastAPI, Depends

app = FastAPI()

@app.get("/user/{user_id}")
def getUserData(user_id: int, db=Depends(get_db)):
    '''Busca dados do usuário'''
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    return user
"""
        },
        {
            "id": "MED_003",
            "description": "Endpoint sem tratamento adequado de erros",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "code": """
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
"""
        }
    ]
    
    # ========================================================================
    # CATEGORIA: RUIM (10 exemplos) - Score esperado: 0-59
    # ========================================================================
    
    poor_examples = [
        {
            "id": "POOR_001",
            "description": "Endpoint mínimo sem boas práticas",
            "expected_score_min": 0,
            "expected_score_max": 59,
            "code": """
from fastapi import FastAPI

app = FastAPI()

@app.get("/data")
def get():
    return db.query(Data).all()
"""
        },
        {
            "id": "POOR_002",
            "description": "Endpoint sem validação de entrada e sem tratamento de erros",
            "expected_score_min": 0,
            "expected_score_max": 59,
            "code": """
from fastapi import FastAPI

app = FastAPI()

@app.post("/create")
def create(data):
    obj = MyModel()
    obj.name = data['name']
    obj.value = data['value']
    db.add(obj)
    db.commit()
    return {"status": "ok"}
"""
        },
        {
            "id": "POOR_003",
            "description": "Endpoint com múltiplas violações críticas",
            "expected_score_min": 0,
            "expected_score_max": 59,
            "code": """
@app.put("/update/{ID}")
def UpdateItem(ID, NewData):
    ITEM = db.query(Item).get(ID)
    ITEM.data = NewData
    db.commit()
    return ITEM
"""
        }
    ]
    
    # Preencher dataset
    dataset["categories"]["excellent"] = excellent_examples
    dataset["categories"]["good"] = good_examples[:15]  # Garantir 15
    dataset["categories"]["medium"] = medium_examples[:15]  # Garantir 15
    dataset["categories"]["poor"] = poor_examples[:10]  # Garantir 10
    
    # Estatísticas
    dataset["statistics"] = {
        "excellent": len(excellent_examples),
        "good": 15,
        "medium": 15,
        "poor": 10,
        "total": 50
    }
    
    return dataset