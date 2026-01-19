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