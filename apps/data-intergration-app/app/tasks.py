from app.sync import SyncProcessor
from app.models import db
from app.helpers import CURRENT_PROCESSING_CONFIG
from flask import current_app
from flask_rq2 import RQ

rq = RQ()


@rq.job
def sync_config(processing_config):
    current_app.config[CURRENT_PROCESSING_CONFIG] = processing_config
    current_app.logger.info('Starting to sync {}'.format(processing_config.customer))
    db.session.add(processing_config)
    sync_processor = SyncProcessor(processing_config)
    if sync_processor.running():
        current_app.logger.info(f'Skipping sync for: {processing_config.customer}. Sync is already in progress.')
    else:
        sync_processor.run_sync()
    current_app.logger.info('Sync for {} completed'.format(processing_config.customer))
