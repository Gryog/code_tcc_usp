from fastapi import FastAPI

app = FastAPI()

@app.get("/data")
def get():
    return db.query(Data).all()