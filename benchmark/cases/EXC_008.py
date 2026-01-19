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