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
        message = request.form.get("text")
        image_url = request.form.get("image-url")
        chat_history = request.form.get("chat-history")

        if "agent-id" not in session.keys():
            session["agent-id"] = id

        response, products, chat_history = AvabotAgent.chat(
            id, chat_history, message, image_url
        )
        return (
            jsonify(
                {
                    "response": response,
                    "products": products,
                    "chat-history": chat_history,
                }
            ),
            201,
        )
    except Exception:
        return (
            jsonify(
                {"response": "There was server error in avabot backend. Try again!"}
            ),
            201,
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0")
