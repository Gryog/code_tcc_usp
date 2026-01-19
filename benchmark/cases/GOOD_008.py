from fastapi import APIRouter

router = APIRouter(tags=["users"])

@router.get("/users/count")
async def get_user_count():
    '''Retorna total de usuários'''
    userCount = 100
    return {"count": userCount}