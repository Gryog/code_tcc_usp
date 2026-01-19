from fastapi import FastAPI, Depends

app = FastAPI()

@app.get("/user/{user_id}")
def getUserData(user_id: int, db=Depends(get_db)):
    '''Busca dados do usuário'''
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    return user