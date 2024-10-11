import datetime
import os
import sys
import logging
from flask import Flask, request, abort
from flask_migrate import Migrate
from app.models import ProcessingConfig, ProcessingEntry  # noqa
from app.producer import produce_sync_tasks
from app.tasks import rq
from app.helpers import ConfigVariableHelper, StackdriverLogFormatter
from app.admin import admin
from flask.logging import default_handler


def create_app(testing=False):
    app = Flask(__name__)

    log_handler = logging.StreamHandler(sys.stdout)
    formatter = StackdriverLogFormatter()
    log_handler.setFormatter(formatter)
    app.logger.addHandler(log_handler)
    app.logger.removeHandler(default_handler)
    app.logger.setLevel(logging.INFO)

    app.config['GOOGLE_CLOUD_PROJECT'] = 'conversionly-235308'
    config_helper = ConfigVariableHelper(
        os.getenv('FLASK_ENV'), app.config.get('GOOGLE_CLOUD_PROJECT'))

    app.config['SQLALCHEMY_DATABASE_URI'] = config_helper.get_variable(
        'POSTGRES_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['RQ_REDIS_URL'] = config_helper.get_variable('REDIS_URL')
    app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
    app.secret_key = config_helper.get_variable('FLASK_SECRET_KEY')

    rq.init_app(app)

    @app.route('/health')
    def health():
        return 'OK'

    @app.route('/trigger_sync')
    def trigger_sync():
        force = request.args.get('force') == 'true'
        num_tasks = produce_sync_tasks(force)
        return 'Produced {} tasks'.format(num_tasks)

    @app.route('/processing_entry_cleanup')
    def remove_old_processing_entries():
        three_months_ago = datetime.datetime.utcnow() - datetime.timedelta(days=90)
        try:
            ProcessingEntry.query.filter(ProcessingEntry.started_at <= three_months_ago).delete()
            db.session.commit()
            return 'Deleted old entries.'
        except Exception as e:
            db.session.rollback()
            app.logger.exception(f'Processing entry cleanup failed: {e}')
            abort(500, 'Processing entry cleanup failed.')

    from app.models import db
    db.init_app(app)
    migrate = Migrate(app, db)  # noqa
    admin.init_app(app)

    return app
