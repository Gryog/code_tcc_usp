from fastapi import APIRouter

router = APIRouter(tags=["users"])

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    '''Busca usuário'''
    return {"id": user_id, "name": "User"}