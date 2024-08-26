from flask import Flask, request, render_template, send_from_directory, jsonify

from app import App

flask_app = Flask(__name__)


@flask_app.route("/")
def index():
    return render_template("index.html")


@flask_app.route("/search")
def search():
    search_query = request.args.get("search_query")

    app = App()
    results = app.search(search_query, results=25)
    relative_paths = [f"images/{image}" for image in results]
    return jsonify(relative_paths)  

@flask_app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('/home/nguyenhoangphuc-22521129/AIC2024/static/HCMAI22_MiniBatch1/Keyframes/', filename)

if __name__ == "__main__":
    flask_app.run(port=5000)
