import json
import os

import requests
from flask import Flask, request, abort
from werkzeug.exceptions import HTTPException

from src import feedparser
from src.exceptions import ApiRequestException
from src.helpers import setup_logging, get_logging_details, generate_request_id

application_root = os.getenv("APPLICATION_ROOT", "/")


def create_app():
    app = Flask(__name__)
    app.config["APPLICATION_ROOT"] = application_root

    setup_logging(app)

    @app.route(
        "/"
    )  # Example feed, see tests/test_app for testing this. Reimplement/remove
    def feed_example():
        r = requests.head("https://icanhazdadjoke.com/")
        if not r.ok:
            app.logger.error(
                "Joke API was not reachable", extra={"request_text": r.text}
            )
            abort(404, "Joke API not available.")
        try:
            joke_amount = request.args.get("jokes", 5)
            return feedparser.create_feed(joke_amount)
        except ApiRequestException as e:
            app.logger.error(e.message, extra=e.extra)
            abort(404, "Could not reach Joke API.")
        except Exception as e:
            app.logger.error(
                "Unexpected error in feed creation.", extra={"error": str(e)}
            )
            abort(500, "Unexpected error occurred.")

    @app.route(
        "/param_test_example"
    )  # Example for testing, see tests/test_app. Free to remove
    def param_test_example():
        param1 = request.args.get("param1", None)
        if not param1:
            abort(404, "Param1 not found.")
        param2 = request.args.get("param2", None)
        if not param2:
            abort(403, "Param2 not found.")
        return "OK"

    @app.errorhandler(
        HTTPException
    )  # Don't remove unless you want more control on error handling
    def handle_exception(e):
        response = e.get_response()
        app.logger.info(e)
        response.data = json.dumps(
            {"code": e.code, "name": e.name, "description": e.description}
        )
        response.content_type = "application/json"
        return response

    @app.route("/health")
    def health_check():
        return "OK"

    @app.before_request
    def before_request():
        request.id = generate_request_id()

    @app.after_request
    def after_request(response):
        path = request.full_path or "Unknown"
        status_code = response.status_code
        if path.startswith("/health"):
            # we don't want to log our health check requests
            return response
        message, extra = get_logging_details(status_code, path)
        app.logger.info(message, extra=extra)
        return response

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
