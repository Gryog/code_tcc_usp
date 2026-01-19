@app.get("/bad-defaults")
def bad_defaults(lista=[]):
    lista.append(1)
    return lista