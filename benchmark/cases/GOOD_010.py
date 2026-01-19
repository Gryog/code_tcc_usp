from fastapi import APIRouter

router = APIRouter(tags=["utils"])

@router.get("/echo")
def echo_message(msg: str):
    '''Retorna a mensagem enviada'''
    return {"message": msg}