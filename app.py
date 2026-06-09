import run as pipeline
import config
from flask import Flask, render_template, jsonify
import io, sys


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/run", methods=["POST"])
def run_pipeline():
    buffer = io.StringIO()
    sys.stdout = buffer   
    exit_code = pipeline.main()
    sys.stdout = sys.__stdout__  # restore normal stdout
    log_tail = buffer.getvalue()
    return jsonify(success=(exit_code == 0), logs=log_tail)


if __name__ == "__main__":
    app.run(debug=True)
