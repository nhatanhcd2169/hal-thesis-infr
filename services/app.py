from flask import Flask, jsonify, request

app = Flask(__name__)

@app.get("/")
def getty():
    return "<p>this is custom API server</p>"

@app.post("/")
def posty():
    body = request.get_json()
    return body
