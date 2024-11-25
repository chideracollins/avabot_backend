from flask import Flask, jsonify, request, session
from flask_cors import CORS

from avabot_backend.avabot_agent import AvabotAgent


app = Flask(__name__)
CORS(app)

app.secret_key = "my-key"


@app.route("/chat", methods=["POST"])
def chat():
    try:
        id = request.form.get("id")
        message = str(request.form.get("text"))

        if "agent-id" not in session.keys():
            session["agent-id"] = id

        response, products = AvabotAgent.chat(id, message)
        print(f"\n\nHere is the list of retrieved products: {products}\n")
        return jsonify({"response": response, "products": products}), 201
    except Exception as e:
        print(e)
        return jsonify({"response": "There was server error in avabot backend."}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0")
