@app.put("/update/{ID}")
def UpdateItem(ID, NewData):
    ITEM = db.query(Item).get(ID)
    ITEM.data = NewData
    db.commit()
    return ITEM