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