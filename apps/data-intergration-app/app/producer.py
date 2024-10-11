from app.models import ProcessingConfig
from app.tasks import sync_config
from flask import current_app


def produce_sync_tasks(force=False):
    configs = ProcessingConfig.get_syncable_configs(force=force)
    current_app.logger.info('Got {} configs. Producing tasks...'.format(len(configs)))
    for config in configs:
        # TODO: reduce timeout down once backfill for Binance.com is done
        sync_config.queue(config, timeout='12h')
    return len(configs)
