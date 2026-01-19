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
    - 10 Excelentes (90-100)
    - 15 Bons (80-89)
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
    # CATEGORIA: EXCELENTE (10 exemplos) - Score esperado: 90-100
    # ========================================================================

    excellent_examples = [
        {
            "id": "EXC_001",
            "description": "Endpoint GET completo com paginação e documentação",
            "expected_score_min": 90,
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
            "expected_score_min": 90,
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
            "expected_score_min": 90,
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
        {
            "id": "EXC_004",
            "description": "Endpoint DELETE com soft delete",
            "expected_score_min": 90,
            "expected_score_max": 100,
            "code": """
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1", tags=["categories"])

@router.delete(
    response_model=DeleteResponse,
    status_code=status.HTTP_200_OK,
    tags=["categories"]
)
async def delete_category(
    category_id: int = Path(..., gt=0, description="ID da categoria"),
    db: Session = Depends(get_db)
) -> DeleteResponse:
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
            "expected_score_min": 90,
            "expected_score_max": 100,
            "code": """
from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Body
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/api/v1", tags=["notifications"])


class EmailSchema(BaseModel):
    email: EmailStr
    subject: str = Field(..., min_length=1, description="Assunto do email")
    content: str = Field(..., min_length=1, description="Conteúdo do email")


class NotificationQueuedResponse(BaseModel):
    message: str


def send_email_background(email: str, subject: str, content: str) -> None:
    # Simula envio de email
    pass


@router.post(
    "/send-email",
    response_model=NotificationQueuedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["notifications"]
)
async def send_notification(
    email_data: EmailSchema = Body(..., description="Dados do email para envio em background"),
    background_tasks: BackgroundTasks = ...
) -> NotificationQueuedResponse:
    '''
    Envia notificação por email em background.

    Args:
        email_data: Dados do email
        background_tasks: Gerenciador de tarefas em background

    Returns:
        Mensagem de confirmação de enfileiramento

    Raises:
        HTTPException: Erro 500 caso falhe ao enfileirar a tarefa
    '''
    try:
        background_tasks.add_task(
            send_email_background,
            email_data.email,
            email_data.subject,
            email_data.content
        )
        return NotificationQueuedResponse(message="Email queued for sending")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao enfileirar envio de email: {str(e)}"
        )
""",
        },
        {
            "id": "EXC_006",
            "description": "Endpoint de Upload de Arquivo com Validação",
            "expected_score_min": 90,
            "expected_score_max": 100,
            "code": """
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["files"])

@router.post(
    "/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["files"]
)
async def upload_file(
    file: UploadFile = File(..., description="Arquivo de imagem (max 5MB)")
) -> FileUploadResponse:
    '''
    Faz upload de um arquivo de imagem.
    '''
    try:
        if not file.content_type.startswith("image/"):
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

        return FileUploadResponse(
            filename=file.filename,
            content_type=file.content_type
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar arquivo"
        )
""",
        },
        {
            "id": "EXC_007",
            "description": "Endpoint de Busca Complexa com Dependência de Filtro",
            "expected_score_min": 90,
            "expected_score_max": 100,
            "code": """
from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional, List
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1", tags=["items"])

@router.get(
    "/search",
    response_model=List[ItemResponse],
    status_code=status.HTTP_200_OK,
    tags=["items"]
)
async def search_items(
    filters: ItemFilter = Depends(parse_filter),
    db: Session = Depends(get_db)
) -> List[ItemResponse]:
    '''
    Busca itens com filtros complexos.
    '''
    try:
        query = db.query(Item)

        if filters.q:
            query = query.filter(Item.name.contains(filters.q))
        if filters.min_price is not None:
            query = query.filter(Item.price >= filters.min_price)
        if filters.max_price is not None:
            query = query.filter(Item.price <= filters.max_price)

        return query.all()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar itens"
        )
""",
        },
        {
            "id": "EXC_008",
            "description": "Endpoint com autenticação OAuth2 e Scopes",
            "expected_score_min": 90,
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
    user_id: int = Path(..., gt=0, description="ID do usuário"),
    current_user: User = Security(get_current_user, scopes=["admin"]),
    db: Session = Depends(get_db)
) -> None:
    '''
    Endpoint administrativo seguro para remoção de usuários.
    '''
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )

        db.delete(user)
        db.commit()
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao remover usuário"
        )
""",
        },
        {
            "id": "EXC_009",
            "description": "Health Check Endpoint Robusto",
            "expected_score_min": 90,
            "expected_score_max": 100,
            "code": """
from fastapi import APIRouter, status, Depends
from sqlalchemy.sql import text

router = APIRouter(tags=["health"])

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    tags=["health"],
    response_model=HealthResponse
)
async def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    '''
    Verifica a saúde da aplicação e conexão com banco.
    '''
    try:
        db.execute(text("SELECT 1"))
        return HealthResponse(status="healthy", database="connected")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Banco indisponível"
        )
""",
        },
        {
            "id": "EXC_010",
            "description": "Endpoint com StreamingResponse",
            "expected_score_min": 90,
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
    # CATEGORIA: BOM (15 exemplos) - Score esperado: 80-89
    # ========================================================================

    good_examples = [
        {
            "id": "GOOD_001",
            "description": "Endpoint sem tags explícitas (mas tem outras boas práticas)",
            "expected_score_min": 80,
            "expected_score_max": 89,
            "code": """
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1")

@router.get(
    "/items",
    response_model=List[ItemResponse],
    status_code=status.HTTP_200_OK,
    tags=["items"]
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
            "expected_score_max": 89,
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao criar tarefa")
""",
        },
        {
            "id": "GOOD_003",
            "description": "Endpoint sem Query() explícito para parâmetros",
            "expected_score_min": 80,
            "expected_score_max": 89,
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
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
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
            "expected_score_max": 89,
            "code": """
from fastapi import APIRouter, Query

router = APIRouter(tags=["search"])

@router.get("/search", status_code=status.HTTP_200_OK, response_model=Dict[str, str], tags=["search"])
async def search(q: Optional[str] = Query(None)) -> Dict[str, str]:
    '''Busca simples'''
    return {"query": q or ""}
""",
        },
        {
            "id": "GOOD_005",
            "description": "Response model genérico Dict",
            "expected_score_min": 80,
            "expected_score_max": 89,
            "expected_keywords": ["response_model", "Dict", "schema", "Pydantic"],
            "code": """
from fastapi import APIRouter, status
from typing import Dict

router = APIRouter(tags=["misc"])

@router.get("/config", response_model=Dict[str, str], status_code=status.HTTP_200_OK, tags=["misc"])
async def get_config() -> Dict[str, str]:
    '''Retorna configurações'''
    return {"version": "1.0", "env": "prod"}
""",
        },
        {
            "id": "GOOD_006",
            "description": "Falta docstring estruturada",
            "expected_score_min": 80,
            "expected_score_max": 89,
            "code": """
from fastapi import APIRouter, status, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/v1", tags=["auth"])

@router.post("/login", status_code=status.HTTP_200_OK, response_model=Dict[str, str], tags=["auth"])
async def login(creds: LoginCtx) -> Dict[str, str]:
    '''Faz login e retorna um token.'''
    try:
        return {"token": "abc"}
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro no login")
""",
        },
        {
            "id": "GOOD_007",
            "description": "Uso de print em vez de logger",
            "expected_score_min": 80,
            "expected_score_max": 89,
            "expected_keywords": ["print", "logger", "logging"],
            "code": """
from fastapi import APIRouter, status

router = APIRouter(tags=["test"])

@router.get("/debug", status_code=status.HTTP_200_OK)
async def debug_endpoint() -> Dict[str, str]:
    '''Endpoint para debug'''
    print("Debug endpoint called")
    return {"status": "ok"}
""",
        },
        {
            "id": "GOOD_008",
            "description": "Mistura de snake_case e camelCase nas variáveis",
            "expected_score_min": 80,
            "expected_score_max": 89,
            "code": """
from fastapi import APIRouter

router = APIRouter(tags=["users"])

@router.get("/users/count", status_code=status.HTTP_200_OK, response_model=Dict[str, int], tags=["users"])
async def get_user_count() -> Dict[str, int]:
    '''Retorna total de usuários'''
    user_count = 100
    return {"count": user_count}
""",
        },
        {
            "id": "GOOD_009",
            "description": "Falta status code explícito 201 no POST",
            "expected_score_min": 80,
            "expected_score_max": 89,
            "code": """
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["items"])

class Item(BaseModel):
    name: str

@router.post("/items", status_code=status.HTTP_201_CREATED)
async def create_item(item: Item):
    '''Cria item'''
    return item
""",
        },
        {
            "id": "GOOD_010",
            "description": "Endpoint síncrono para operação I/O bound simples",
            "expected_score_min": 80,
            "expected_score_max": 89,
            "code": """
from fastapi import APIRouter

router = APIRouter(tags=["utils"])

@router.get("/echo", status_code=status.HTTP_200_OK, response_model=Dict[str, str], tags=["utils"])
def echo_message(msg: str = Query(...)) -> Dict[str, str]:
    '''Retorna a mensagem enviada'''
    return {"message": msg}
""",
        },
        {
            "id": "GOOD_011",
            "description": "Validação de entrada manual simples, poderia ser Pydantic",
            "expected_score_min": 80,
            "expected_score_max": 89,
            "code": """
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["calc"])

@router.get("/divide", status_code=status.HTTP_200_OK, response_model=Dict[str, float], tags=["calc"])
async def divide(a: int, b: int) -> Dict[str, float]:
    '''Faz divisão'''
    if b == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Zero division")
    return {"result": a / b}
""",
        },
        {
            "id": "GOOD_012",
            "description": "Path parameter sem type hint int explícito na rota",
            "expected_score_min": 80,
            "expected_score_max": 89,
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
            "expected_score_max": 89,
            "code": """
from fastapi import APIRouter
from typing import List

router = APIRouter(tags=["tags"])

@router.get("/tags", response_model=List[str], status_code=status.HTTP_200_OK, tags=["tags"])
async def get_tags() -> List[str]:
    '''Lista todas as tags'''
    return ["tag1", "tag2"]
""",
        },
        {
            "id": "GOOD_014",
            "description": "Falta response_model, mas implementação é limpa",
            "expected_score_min": 80,
            "expected_score_max": 89,
            "code": """
from fastapi import APIRouter, status

router = APIRouter(tags=["status"])

@router.get("/ping", status_code=status.HTTP_200_OK, response_model=Dict[str, str], tags=["status"])
async def ping() -> Dict[str, str]:
    '''Health check simples'''
    return {"ping": "pong"}
""",
        },
        {
            "id": "GOOD_015",
            "description": "Usa Form em vez de Pydantic JSON Body para dados estruturados",
            "expected_score_min": 80,
            "expected_score_max": 89,
            "code": """
from fastapi import APIRouter, Form

router = APIRouter(tags=["login"])

@router.post("/login-form", status_code=status.HTTP_200_OK, response_model=Dict[str, str], tags=["login"])
async def login_form(username: str = Form(...), password: str = Form(...)) -> Dict[str, str]:
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
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/api/v1", tags=["customers"])

@router.get("/customers", status_code=status.HTTP_200_OK, response_model=List[dict])
async def get_customers(db: Session = Depends(get_db)) -> List[dict]:
    '''Retorna lista de clientes'''
    try:
        customers = db.query(Customer).all()
        return customers
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao buscar clientes")

""",
        },
        {
            "id": "MED_002",
            "description": "Endpoint com nome inadequado e sem type hints completos",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "code": """
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

app = FastAPI()

@app.get("/user/{user_id}", status_code=status.HTTP_200_OK)
def get_user_data(user_id: int, db: Session = Depends(get_db)):
    '''Busca dados do usuário'''
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return user

""",
        },
        {
            "id": "MED_003",
            "description": "Endpoint sem tratamento adequado de erros",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "code": """
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session

router = APIRouter(tags=["invoices"])

@router.get(
    "/invoices/{invoice_id}",
    response_model=InvoiceResponse,
    status_code=status.HTTP_200_OK,
    tags=["invoices"]
)
async def get_invoice(
    invoice_id: int = Path(..., gt=0),
    db: Session = Depends(get_db)
) -> InvoiceResponse:
    '''Busca fatura por ID'''
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
        return invoice
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao buscar fatura")

""",
        },
        {
            "id": "MED_004",
            "description": "Tratamento de erro genérico (Exception)",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "code": """
from fastapi import APIRouter, HTTPException, status
from typing import Dict

router = APIRouter(tags=["risky"])

@router.get("/risky", status_code=status.HTTP_200_OK, response_model=Dict[str, str], tags=["risky"])
async def risky_op() -> Dict[str, str]:
    '''Executa operação arriscada'''
    try:
        return {"status": "ok"}
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error")

""",
        },
        {
            "id": "MED_005",
            "description": "Sem type hints nos parâmetros",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "code": """
from fastapi import APIRouter, status
from typing import Dict

router = APIRouter(tags=["calc"])

@router.get("/calc", status_code=status.HTTP_200_OK, response_model=Dict[str, int], tags=["calc"])
async def calculate(x: int, y: int) -> Dict[str, int]:
    '''Calcula soma'''
    return {"sum": x + y}

""",
        },
        {
            "id": "MED_006",
            "description": "Blocking IO em função async",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "expected_keywords": ["blocking", "bloqueante", "async", "def", "threadpool", "run_in_executor"],
            "code": """
from fastapi import APIRouter, status
from typing import Dict
import asyncio

router = APIRouter(tags=["sleep"])

@router.get("/sleep", status_code=status.HTTP_200_OK, response_model=Dict[str, str], tags=["sleep"])
async def sleep_route() -> Dict[str, str]:
    '''Simula espera sem bloquear o loop'''
    await asyncio.sleep(1)
    return {"status": "awake"}

""",
        },
        {
            "id": "MED_007",
            "description": "Retorna dicionário cru sem schema",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "code": """
from fastapi import APIRouter, status
from typing import Dict, Any

router = APIRouter(tags=["data"])

@router.get("/data", status_code=status.HTTP_200_OK, response_model=Dict[str, Any], tags=["data"])
async def get_data() -> Dict[str, Any]:
    '''Retorna dados simples'''
    return {"a": 1, "b": 2, "c": [1, 2, 3]}

""",
        },
        {
            "id": "MED_008",
            "description": "Não usa APIRouter, usa app direto (misturado)",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "code": """
from fastapi import FastAPI, status
from typing import Dict

app = FastAPI()

@app.get("/direct", status_code=status.HTTP_200_OK, response_model=Dict[str, str])
def direct_route() -> Dict[str, str]:
    '''Rota direta'''
    return {"status": "ok"}

""",
        },
        {
            "id": "MED_009",
            "description": "Uso incorreto de status codes (200 para erro)",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "code": """
from fastapi import APIRouter, HTTPException, status
from typing import Dict

router = APIRouter(tags=["check"])

@router.get("/check/{id}", status_code=status.HTTP_200_OK, response_model=Dict[str, int], tags=["check"])
async def check(id: int) -> Dict[str, int]:
    '''Valida ID'''
    if id < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID")
    return {"id": id}

""",
        },
        {
            "id": "MED_010",
            "description": "Lógica de negócio complexa dentro da view/rota",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "code": """
from fastapi import APIRouter, status
from typing import Dict

router = APIRouter(tags=["process"])

@router.post("/process", status_code=status.HTTP_200_OK, response_model=Dict[str, int], tags=["process"])
async def process_data(data: Dict[str, int]) -> Dict[str, int]:
    '''Processa dados numéricos'''
    res = 0
    for _, v in data.items():
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
from fastapi import APIRouter, status
from typing import Dict

router = APIRouter(tags=["users"])

@router.get("/user-info", status_code=status.HTTP_200_OK, response_model=Dict[str, str], tags=["users"])
async def get_user_info() -> Dict[str, str]:
    '''Retorna info do usuário'''
    return {"user": "info"}

""",
        },
        {
            "id": "MED_012",
            "description": "Query param sem validação (SQL Injection vulnerability potencial se mal usado)",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "code": """
from fastapi import APIRouter, status, Query
from typing import Dict

router = APIRouter(tags=["filter"])

@router.get("/filter", status_code=status.HTTP_200_OK, response_model=Dict[str, str], tags=["filter"])
async def filter_items(where: str = Query(..., min_length=1, description="Filtro (não usar SQL raw)")) -> Dict[str, str]:
    '''Filtra itens (exemplo)'''
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
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Dict

router = APIRouter(tags=["db"])

@router.get("/db-test", status_code=status.HTTP_200_OK, response_model=Dict[str, str], tags=["db"])
async def db_test(db: Session = Depends(get_db)) -> Dict[str, str]:
    '''Teste simples de acesso ao DB'''
    return {"status": "ok"}

""",
        },
        {
            "id": "MED_014",
            "description": "Usa variáveis globais",
            "expected_score_min": 60,
            "expected_score_max": 79,
            "code": """
from fastapi import APIRouter, status
from typing import Dict

router = APIRouter(tags=["count"])
COUNTER = 0

@router.get("/count", status_code=status.HTTP_200_OK, response_model=Dict[str, int], tags=["count"])
async def get_count() -> Dict[str, int]:
    '''Incrementa contador global'''
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
from fastapi import APIRouter, status
from typing import Dict, Any

router = APIRouter(tags=["submit"])

@router.post("/submit", status_code=status.HTTP_200_OK, response_model=Dict[str, bool], tags=["submit"])
async def submit(data: Dict[str, Any]) -> Dict[str, bool]:
    '''Recebe dados e confirma recebimento'''
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
