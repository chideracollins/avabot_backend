from flask import Flask, jsonify, request, session

from avabot_backend.avabot_agent import AvabotAgent


app = Flask(__name__)

app.secret_key = "my-key"


@app.route("/chat", methods=["POST"])
def chat():
    id = request.form["id"]
    if "agent-id" not in session.keys():
        session["agent-id"] = id
    message = request.form["text"]
    response, products = AvabotAgent.chat(id, message, dev=False)
    return jsonify({"response": response, "products": products})

if __name__ == "__main__":
    app.run(host="0.0.0.0")
