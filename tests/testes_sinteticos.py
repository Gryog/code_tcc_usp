# SISTEMA COMPLETO DE TESTES PARA VALIDADOR FASTAPI
# Inclui: 50 casos sintéticos + Coleta automática + Análise estatística
# ============================================================================

from datetime import datetime

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
            "description": "Casos sintéticos para validação de código FastAPI",
        },
        "categories": {"excellent": [], "good": [], "medium": [], "poor": []},
        "statistics": {},
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
""",
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
""",
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
""",
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
""",
        },
        {
            "id": "EXC_005",
            "description": "Endpoint com Background Tasks e status 202",
            "expected_score_min": 95,
            "expected_score_max": 100,
            "code": """
from fastapi import APIRouter, BackgroundTasks, status
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api/v1", tags=["notifications"])

class EmailSchema(BaseModel):
    email: EmailStr
    subject: str
    content: str

def send_email_background(email: str, content: str):
    # Simula envio de email
    pass

@router.post(
    "/send-email",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["notifications"]
)
async def send_notification(
    email_data: EmailSchema,
    background_tasks: BackgroundTasks
) -> dict:
    '''
    Envia notificação por email em background.
    
    Args:
        email_data: Dados do email
        background_tasks: Gerenciador de tarefas em background
        
    Returns:
        Mensagem de confirmação
    '''
    background_tasks.add_task(send_email_background, email_data.email, email_data.content)
    return {"message": "Email queued for sending"}
""",
        },
        {
            "id": "EXC_006",
            "description": "Endpoint de Upload de Arquivo com Validação",
            "expected_score_min": 95,
            "expected_score_max": 100,
            "code": """
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from typing import Dict

router = APIRouter(prefix="/api/v1", tags=["files"])

@router.post(
    "/upload",
    response_model=Dict[str, str],
    status_code=status.HTTP_201_CREATED,
    tags=["files"]
)
async def upload_file(
    file: UploadFile = File(..., description="Arquivo de imagem (max 5MB)")
) -> Dict[str, str]:
    '''
    Faz upload de um arquivo de imagem.
    
    Args:
        file: Arquivo enviado pelo cliente
        
    Returns:
        Metadados do arquivo salvo
        
    Raises:
        HTTPException: Se arquivo não for imagem ou muito grande
    '''
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas imagens são permitidas"
        )
    
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Arquivo muito grande (max 5MB)"
        )
        
    return {"filename": file.filename, "content_type": file.content_type}
""",
        },
        {
            "id": "EXC_007",
            "description": "Endpoint de Busca Complexa com Dependência de Filtro",
            "expected_score_min": 95,
            "expected_score_max": 100,
            "code": """
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
""",
        },
        {
            "id": "EXC_008",
            "description": "Endpoint com autenticação OAuth2 e Scopes",
            "expected_score_min": 95,
            "expected_score_max": 100,
            "code": """
from fastapi import APIRouter, Depends, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes

router = APIRouter(prefix="/api/v1", tags=["admin"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", scopes={"admin": "Acesso administrativo"})

async def get_current_user(security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)):
    # Lógica de validação de token e escopo
    pass

@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["admin"]
)
async def delete_user_admin(
    user_id: int,
    current_user: User = Security(get_current_user, scopes=["admin"]),
    db: Session = Depends(get_db)
) -> None:
    '''Endpoint administrativo seguro para remoção de usuários.'''
    # Lógica de deleção
    pass
""",
        },
        {
            "id": "EXC_009",
            "description": "Health Check Endpoint Robusto",
            "expected_score_min": 95,
            "expected_score_max": 100,
            "code": """
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
""",
        },
        {
            "id": "EXC_010",
            "description": "Endpoint com StreamingResponse",
            "expected_score_min": 95,
            "expected_score_max": 100,
            "code": """
from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse
import io

router = APIRouter(prefix="/api/v1", tags=["export"])

@router.get(
    "/export/csv",
    status_code=status.HTTP_200_OK,
    tags=["export"]
)
async def export_data_csv() -> StreamingResponse:
    '''
    Exporta dados em formato CSV via stream.
    '''
    stream = io.StringIO()
    stream.write("id,name,value\\n")
    stream.write("1,Test,100\\n")
    stream.seek(0)
    
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=data.csv"}
    )
""",
        },
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
""",
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
""",
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
""",
        },
        {
            "id": "GOOD_004",
            "description": "Faltam tags e description no Query",
            "expected_score_min": 80,
            "expected_score_max": 94,
            "code": """
from fastapi import APIRouter, Query

router = APIRouter()

@router.get("/search")
async def search(q: str = Query(None)):
    '''Busca simples'''
    return {"query": q}
""",
        },
        {
            "id": "GOOD_005",
            "description": "Response model genérico Dict",
            "expected_score_min": 80,
            "expected_score_max": 94,
            "expected_keywords": ["response_model", "Dict", "schema", "Pydantic"],
            "code": """
from fastapi import APIRouter, status
from typing import Dict

router = APIRouter(tags=["misc"])

@router.get("/config", response_model=Dict, status_code=status.HTTP_200_OK)
async def get_config() -> Dict:
    '''Retorna configurações'''
    return {"version": "1.0", "env": "prod"}
""",
        },
        {
            "id": "GOOD_006",
            "description": "Falta docstring estruturada",
            "expected_score_min": 80,
            "expected_score_max": 94,
            "code": """
from fastapi import APIRouter, status, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/v1", tags=["auth"])

class LoginCtx(BaseModel):
    username: str
    password: str

@router.post("/login", status_code=status.HTTP_200_OK)
async def login(creds: LoginCtx):
    # Faz login
    return {"token": "abc"}
""",
        },
        {
            "id": "GOOD_007",
            "description": "Uso de print em vez de logger",
            "expected_score_min": 80,
            "expected_score_max": 94,
            "expected_keywords": ["print", "logger", "logging"],
            "code": """
from fastapi import APIRouter, status

router = APIRouter(tags=["test"])

@router.get("/debug", status_code=status.HTTP_200_OK)
async def debug_endpoint():
    '''Endpoint para debug'''
    print("Debug endpoint called")
    return {"status": "ok"}
""",
        },
        {
            "id": "GOOD_008",
            "description": "Mistura de snake_case e camelCase nas variáveis",
            "expected_score_min": 80,
            "expected_score_max": 94,
            "code": """
from fastapi import APIRouter

router = APIRouter(tags=["users"])

@router.get("/users/count")
async def get_user_count():
    '''Retorna total de usuários'''
    userCount = 100
    return {"count": userCount}
""",
        },
        {
            "id": "GOOD_009",
            "description": "Falta status code explícito 201 no POST",
            "expected_score_min": 80,
            "expected_score_max": 94,
            "code": """
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["items"])

class Item(BaseModel):
    name: str

@router.post("/items")
async def create_item(item: Item):
    '''Cria item'''
    return item
""",
        },
        {
            "id": "GOOD_010",
            "description": "Endpoint síncrono para operação I/O bound simples",
            "expected_score_min": 80,
            "expected_score_max": 94,
            "code": """
from fastapi import APIRouter

router = APIRouter(tags=["utils"])

@router.get("/echo")
def echo_message(msg: str):
    '''Retorna a mensagem enviada'''
    return {"message": msg}
""",
        },
        {
            "id": "GOOD_011",
            "description": "Validação de entrada manual simples, poderia ser Pydantic",
            "expected_score_min": 80,
            "expected_score_max": 94,
            "code": """
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["calc"])

@router.get("/divide")
async def divide(a: int, b: int):
    '''Faz divisão'''
    if b == 0:
        raise HTTPException(status_code=400, detail="Zero division")
    return {"result": a / b}
""",
        },
        {
            "id": "GOOD_012",
            "description": "Path parameter sem type hint int explícito na rota",
            "expected_score_min": 80,
            "expected_score_max": 94,
            "code": """
from fastapi import APIRouter

router = APIRouter(tags=["users"])

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    '''Busca usuário'''
    return {"id": user_id, "name": "User"}
""",
        },
        {
            "id": "GOOD_013",
            "description": "Retorna lista direta sem wrapping object (ok, mas menos evoluível)",
            "expected_score_min": 80,
            "expected_score_max": 94,
            "code": """
from fastapi import APIRouter
from typing import List

router = APIRouter(tags=["tags"])

@router.get("/tags", response_model=List[str])
async def get_tags():
    '''Lista todas as tags'''
    return ["tag1", "tag2"]
""",
        },
        {
            "id": "GOOD_014",
            "description": "Falta response_model, mas implementação é limpa",
            "expected_score_min": 80,
            "expected_score_max": 94,
            "code": """
from fastapi import APIRouter, status

router = APIRouter(tags=["status"])

@router.get("/ping", status_code=status.HTTP_200_OK)
async def ping():
    '''Health check simples'''
    return {"ping": "pong"}
""",
        },
        {
            "id": "GOOD_015",
            "description": "Usa Form em vez de Pydantic JSON Body para dados estruturados",
            "expected_score_min": 80,
            "expected_score_max": 94,
            "code": """
from fastapi import APIRouter, Form

router = APIRouter(tags=["login"])

@router.post("/login-form")
async def login_form(username: str = Form(...), password: str = Form(...)):
    '''Login via form data'''
    return {"user": username}
""",
        },
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
""",
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
""",
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
""",
        },
        {
            "id": "MED_004",
            "description": "Tratamento de erro genérico (Exception)",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "code": """
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/risky")
async def risky_op():
    try:
        # op
        pass
    except Exception:
        raise HTTPException(status_code=500, detail="Error")
""",
        },
        {
            "id": "MED_005",
            "description": "Sem type hints nos parâmetros",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "code": """
from fastapi import APIRouter

router = APIRouter()

@router.get("/calc")
async def calculate(x, y):
    return {"sum": int(x) + int(y)}
""",
        },
        {
            "id": "MED_006",
            "description": "Blocking IO em função async",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "expected_keywords": ["blocking", "bloqueante", "async", "def", "threadpool", "run_in_executor"],
            "code": """
from fastapi import APIRouter
import time

router = APIRouter()

@router.get("/sleep")
async def sleep_route():
    time.sleep(1) # Bloqueia o loop
    return {"status": "awake"}
""",
        },
        {
            "id": "MED_007",
            "description": "Retorna dicionário cru sem schema",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "code": """
from fastapi import APIRouter

router = APIRouter()

@router.get("/data")
async def get_data():
    return {"a": 1, "b": 2, "c": [1,2,3]}
""",
        },
        {
            "id": "MED_008",
            "description": "Não usa APIRouter, usa app direto (misturado)",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "code": """
from fastapi import FastAPI

app = FastAPI()

@app.get("/direct")
def direct_route():
    return "ok"
""",
        },
        {
            "id": "MED_009",
            "description": "Uso incorreto de status codes (200 para erro)",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "code": """
from fastapi import APIRouter

router = APIRouter()

@router.get("/check/{id}")
async def check(id: int):
    if id < 0:
        return {"error": "Invalid ID"} # Retorna 200 OK com erro no body
    return {"id": id}
""",
        },
        {
            "id": "MED_010",
            "description": "Lógica de negócio complexa dentro da view/rota",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "code": """
from fastapi import APIRouter

router = APIRouter()

@router.post("/process")
async def process_data(data: dict):
    # Lógica complexa aqui
    res = 0
    for k, v in data.items():
        if isinstance(v, int):
            res += v * 2
    return {"result": res}
""",
        },
        {
            "id": "MED_011",
            "description": "Nome de rota inconsistente (CamelCase no path)",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "code": """
from fastapi import APIRouter

router = APIRouter()

@router.get("/getUserInfo")
async def get_user_info():
    return {"user": "info"}
""",
        },
        {
            "id": "MED_012",
            "description": "Query param sem validação (SQL Injection vulnerability potencial se mal usado)",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "code": """
from fastapi import APIRouter

router = APIRouter()

@router.get("/filter")
async def filter_items(where: str):
    # Recebe cláusula raw, perigoso
    return {"query": f"SELECT * FROM items WHERE {where}"}
""",
        },
        {
            "id": "MED_013",
            "description": "Falta injeção de dependência para DB (hardcoded)",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "expected_keywords": ["hardcoded", "dependency injection", "depends", "db session"],
            "code": """
from fastapi import APIRouter

router = APIRouter()

@router.get("/db-test")
async def db_test():
    conn = "sqlite:///db.sqlite" # Hardcoded
    return {"conn": conn}
""",
        },
        {
            "id": "MED_014",
            "description": "Usa variáveis globais",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "code": """
from fastapi import APIRouter

router = APIRouter()
COUNTER = 0

@router.get("/count")
async def get_count():
    global COUNTER
    COUNTER += 1
    return {"count": COUNTER}
""",
        },
        {
            "id": "MED_015",
            "description": "Falta de docstring total",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "code": """
from fastapi import APIRouter

router = APIRouter()

@router.post("/submit")
async def submit(data: dict):
    return {"received": True}
""",
        },
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
""",
        },
        {
            "id": "POOR_002",
            "description": "Endpoint sem validação de entrada e sem tratamento de erros",
            "expected_score_min": 0,
            "expected_score_max": 59,
            "expected_keywords": ["validation", "pydantic", "schema", "type hint", "error handling"],
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
""",
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
""",
        },
        {
            "id": "POOR_004",
            "description": "Retorno de HTML em rota API JSON (sem response class)",
            "expected_score_min": 0,
            "expected_score_max": 59,
            "code": """
@app.get("/home")
def home():
    return "<h1>Hello</h1>"
""",
        },
        {
            "id": "POOR_005",
            "description": "Uso de eval() perigoso",
            "expected_score_min": 0,
            "expected_score_max": 59,
            "expected_keywords": ["eval", "exec", "security", "code injection", "rce"],
            "code": """
@app.post("/calc")
def calc(expr: str):
    return eval(expr)
""",
        },
        {
            "id": "POOR_006",
            "description": "Rota sem verbo HTTP defindo (ex: usa add_api_route incorretamente ou lógica obscura)",
            "expected_score_min": 0,
            "expected_score_max": 59,
            "code": """
def my_route(req):
    return {"a":1}
    
app.add_api_route("/weird", my_route)
""",
        },
        {
            "id": "POOR_007",
            "description": "Captura de exceção vazia (pass)",
            "expected_score_min": 0,
            "expected_score_max": 59,
            "code": """
@app.get("/silent")
def silent_error():
    try:
        1/0
    except:
        pass
    return "ok"
""",
        },
        {
            "id": "POOR_008",
            "description": "Dados sensíveis no retorno (senha)",
            "expected_score_min": 0,
            "expected_score_max": 59,
            "expected_keywords": ["password", "senha", "hash", "leak", "security", "response_model"],
            "code": """
@app.get("/user/{id}")
def get_user_bad(id):
    user = db.get(id)
    return {"user": user.name, "password": user.password_hash}
""",
        },
        {
            "id": "POOR_009",
            "description": "Loop infinito sem async/await (DoS)",
            "expected_score_min": 0,
            "expected_score_max": 59,
            "expected_keywords": ["loop", "infinite", "dos", "block", "cpu"],
            "code": """
@app.get("/hang")
def hang():
    while True:
        pass
""",
        },
        {
            "id": "POOR_010",
            "description": "Modificação de argumentos padrão mutáveis",
            "expected_score_min": 0,
            "expected_score_max": 59,
            "code": """
@app.get("/bad-defaults")
def bad_defaults(lista=[]):
    lista.append(1)
    return lista
""",
        },
    ]

    # Preencher dataset
    dataset["categories"]["excellent"] = excellent_examples
    dataset["categories"]["good"] = good_examples
    dataset["categories"]["medium"] = medium_examples
    dataset["categories"]["poor"] = poor_examples

    # Estatísticas
    dataset["statistics"] = {
        "excellent": len(excellent_examples),
        "good": len(good_examples),
        "medium": len(medium_examples),
        "poor": len(poor_examples),
        "total": len(excellent_examples)
        + len(good_examples)
        + len(medium_examples)
        + len(poor_examples),
    }

    return dataset
