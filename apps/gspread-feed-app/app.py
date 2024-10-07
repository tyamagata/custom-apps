import os
import argon2
import gspread
from flask import Flask, request, make_response, abort
from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics

from src import feed_parser
from src.helpers import (
    setup_logging,
    get_credentials,
    get_users,
    get_logging_details,
    generate_request_id,
    get_worksheets_config,
)

application_root = os.getenv("APPLICATION_ROOT", "/")


def create_app():  # noqa: max-complexity=30
    app = Flask(__name__)
    app.config["APPLICATION_ROOT"] = application_root

    setup_logging(app)

    metrics = GunicornPrometheusMetrics(app, defaults_prefix="feed_apps")

    @app.route("/")
    def index():
        spreadsheet_id, company_id, password = get_request_params(request)

        worksheets_config = get_worksheets_config()

        if worksheets_config and spreadsheet_id in worksheets_config:
            worksheet_name = worksheets_config[spreadsheet_id]
        else:
            worksheet_name = None

        try:
            service_account_credentials = get_credentials()
            sheet_passwords = get_users()
        except Exception as e:
            app.logger.exception(f"An error occured when retrieving secrets: {e}")
            abort(500, "Something went wrong. Please contact your account manager.")

        authenticate_request(company_id, password, spreadsheet_id, sheet_passwords)

        try:
            client = gspread.authorize(service_account_credentials)
        except AttributeError:
            app.logger.error(
                f"Could not access spreadsheet id: {spreadsheet_id} with stored service account."
            )
            abort(
                500,
                "Make sure you shared the google spreadsheet with the correct email address.",
            )

        app.logger.info("service account authorized")

        try:
            ss = client.open_by_key(spreadsheet_id)
            sheet = (
                ss.worksheet(worksheet_name) if worksheet_name else ss.get_worksheet(0)
            )
        except Exception as e:
            app.logger.error(f"Spreadsheet not found: {spreadsheet_id}. Message: {e}")
            abort(
                404,
                f"The spreadsheet was not found: {spreadsheet_id}. Please check if the Id is \
                    correct",
            )

        try:
            sendable_file = feed_parser.write_to_csv(sheet.get_all_values())
            app.logger.info("feed found and saved")
            output = make_response(sendable_file)
            output.headers["Content-Disposition"] = "attachment; filename=export.csv"
            output.headers["Content-type"] = "text/csv"
            return output
        except FileNotFoundError as fnf_e:
            app.logger.error(
                f"There was an error exporting the spreadsheet: {spreadsheet_id}. Message: {fnf_e}"
            )
            abort(
                404,
                f"There was an error exporting: {spreadsheet_id}. Please check if spreadsheet data \
                    is valid",
            )

    def authenticate_request(company_id, password, spreadsheet_id, sheet_passwords):
        ph = argon2.PasswordHasher()
        try:
            sheet_password = sheet_passwords[spreadsheet_id]
        except KeyError:
            abort(404, "Account credentials not found")
        try:
            if ph.verify(sheet_password, password):
                pass
        except argon2.exceptions.VerifyMismatchError:
            abort(403, "Failed to authenticate")

    def get_request_params(request):
        try:
            input_ss_id = request.args["spreadsheet"]
        except KeyError:
            abort(400, "Spreadsheet id parameter is missing")
        auth = request.authorization
        try:
            if auth.username and auth.password:
                return input_ss_id, auth.username, auth.password
        except AttributeError:
            abort(401, "Access Denied")

    @app.route("/health")
    @metrics.do_not_track()
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
