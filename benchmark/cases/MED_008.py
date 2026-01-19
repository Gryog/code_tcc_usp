from fastapi import FastAPI

app = FastAPI()

@app.get("/direct")
def direct_route():
    return "ok"