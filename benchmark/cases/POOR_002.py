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