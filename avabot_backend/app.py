from flask import Flask


app = Flask()

app.secret_key = "my-key"


@app.route("/chat", methods=["POST"])
def chat():
    pass
