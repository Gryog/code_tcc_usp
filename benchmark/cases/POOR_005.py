@app.post("/calc")
def calc(expr: str):
    return eval(expr)