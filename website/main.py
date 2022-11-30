import json
from quart import Quart, render_template, request, session, redirect, url_for

app = Quart(__name__)


@app.route("/")
async def home():
    return await render_template("index.html")

if __name__ == "__main__":
    # app.run()
    app.run(host="0.0.0.0", port=80)
