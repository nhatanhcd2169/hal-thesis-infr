from flask import Flask, jsonify, request

app = Flask(__name__)

@app.get("/")
def getty():
    return "<p>clmm!!!!</p>"

@app.post("/")
def posty():
    body = request.get_json()
    return body