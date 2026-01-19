@app.get("/silent")
def silent_error():
    try:
        1/0
    except:
        pass
    return "ok"