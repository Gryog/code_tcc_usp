@app.get("/user/{id}")
def get_user_bad(id):
    user = db.get(id)
    return {"user": user.name, "password": user.password_hash}