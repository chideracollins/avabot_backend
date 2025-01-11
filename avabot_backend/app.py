from flask import Flask, jsonify, request, session
from flask_cors import CORS

from avabot_backend.avabot_agent import AvabotAgent


app = Flask(__name__)
CORS(app)

app.secret_key = "my-key"


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        id = data("id")
        message = data("text")
        image_url = data("image-url")
        chat_history = data("chat-history")

        if "agent-id" not in session.keys():
            session["agent-id"] = id

        if message is None:
            message = "Do you sell this product?"

        response, products, chat_history = AvabotAgent.chat(
            id, chat_history, message, image_url
        )
        payload = {"response": response}

        if products:
            payload["products"] = products

        if chat_history:
            payload["chat-history"] = chat_history

        return (
            jsonify(payload),
            201,
        )
    except Exception:
        if chat_history:
            return (
                jsonify(
                    {
                        "response": "There was server error in avabot backend. Try again!",
                        "chat-history": chat_history,
                    }
                ),
                201,
            )

        return (
            jsonify(
                {
                    "response": "There was server error in avabot backend. Try again!",
                }
            ),
            201,
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0")
