from flask import Flask
import os
import requests
from google.auth.transport.requests import Request
from google.oauth2 import id_token

app = Flask(__name__)

RECEIVER_URL = os.environ["RECEIVER_URL"]


@app.get("/")
def index():
    request = Request()

    token = id_token.fetch_id_token(
        request,
        RECEIVER_URL,
    )

    response = requests.get(
        RECEIVER_URL,
        headers={
            "Authorization": f"Bearer {token}",
        },
        timeout=10,
    )

    return (
        f"Caller invoked receiver.\n"
        f"Receiver HTTP status: {response.status_code}\n"
        f"Receiver response: {response.text}"
    ), response.status_code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
