def my_route(req):
    return {"a":1}
    
app.add_api_route("/weird", my_route)