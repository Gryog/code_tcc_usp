from fastapi import APIRouter, Form

router = APIRouter(tags=["login"])

@router.post("/login-form")
async def login_form(username: str = Form(...), password: str = Form(...)):
    '''Login via form data'''
    return {"user": username}