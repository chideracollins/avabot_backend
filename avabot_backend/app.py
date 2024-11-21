from flask import Flask, jsonify, request, session

from avabot_backend.avabot_agent import AvabotAgent


app = Flask()

app.secret_key = "my-key"


@app.route("/chat", methods=["POST"])
def chat():
    id = request.form["id"]
    if "agent-id" not in session.keys():
        session["agent-id"] = id
    message = request.form["text"]
    response, products = AvabotAgent.chat(id, message, dev=False)
    return jsonify({"response": response, "products": products})
