from datetime import datetime
from urllib.parse import urlparse

from app.models import ProcessingEntry, db
from app.ftp import get_files_in_sftp_url, get_files_in_ftp_url
from app.http import get_file_from_url
from app.s3 import get_latest_file_from_s3
from app.converse import ConverseCampaignSender, ConverseAdSender
from app.custom_conversions import CustomConversionSender
from app.server_to_server import ServerToServerSender
from app.multiplatform_server_to_server import MultiplatformServerToServerSender
from app.aggregate_multiplatform_server_to_server import AggregateMultiplatformServerToServerSender
from flask import current_app
from liquid import Environment


class SyncException(Exception):
    pass


class SyncProcessor:
    def __init__(self, config):
        self.config = config
        self._readers = []

    def running(self):
        if self.config.last_processing_started_at is None:
            return False
        elif self.config.last_processed_at is None:
            return True
        elif self.config.last_processing_started_at > self.config.last_processed_at:
            return True
        else:
            return False

    def get_readers(self):
        parsed_url = urlparse(self.config.file_url)
        if parsed_url.scheme == 'sftp':
            return get_files_in_sftp_url(
                parsed_url.hostname,
                self.config.connection_username,
                self.config.connection_password,
                self.config.connection_path,
                self.config.connection_port,
                self.config.last_successfully_processed_at,
                self.config.check_subdirs)
        elif 'ftp' in parsed_url.scheme == 'ftp':
            return get_files_in_ftp_url(
                parsed_url.hostname,
                self.config.connection_username,
                self.config.connection_password,
                self.config.connection_path,
                self.config.connection_port,
                self.config.last_successfully_processed_at)
        elif 'http' in parsed_url.scheme:
            env = Environment()
            env.add_filter("fromtimestamp", datetime.fromtimestamp)
            resolved_url = env.from_string(self.config.file_url).render()
            return [get_file_from_url(resolved_url)]
        elif 's3' in parsed_url.scheme:
            return get_latest_file_from_s3(
                parsed_url.netloc, parsed_url.path,
                self.config.connection_username,
                self.config.last_successfully_processed_at
            )
        else:
            raise SyncException(
                f'No download handler for file_url {self.config.file_url}')

    def run_sync(self):
        self.config.last_processing_started_at = datetime.now()
        db.session.commit()

        try:
            self._readers = self.get_readers()
            self.handle_readers()
            self.config.last_successfully_processed_at = datetime.now()
            self.config.last_processed_at = datetime.now()
            db.session.commit()
        except Exception as e:
            current_app.logger.exception(
                f'Fatal error in sync for {self.config}',
                extra={'error': e}
            )
            self.config.last_processed_at = datetime.now()
            db.session.commit()
            raise e

    def handle_custom_conversion_import(self, parser):
        if self.config.field_mapping:
            custom_conversion_data = parser.to_custom_conversions(self.config.field_mapping)
        else:
            custom_conversion_data = parser.to_custom_conversions()
        result = self.send_custom_conversions(custom_conversion_data)
        return result

    def handle_s2s_import(self, parser):
        events = parser.to_s2s_events()
        result = self.send_s2s_events(events)
        return result

    def handle_multiplatform_s2s_import(self, parser):
        if self.config.field_mapping:
            events = parser.to_multiplatform_s2s_events(
                self.config.field_mapping)
        else:
            events = parser.to_multiplatform_s2s_events()
        sender = MultiplatformServerToServerSender(
            events, self.config.api_token_env_variable, self.config.s2s_token)
        return sender.send()

    def handle_aggregate_multiplatform_s2s_import(self, parser):
        if self.config.field_mapping:
            events = parser.to_aggregate_multiplatform_s2s_events(
                self.config.field_mapping)
        else:
            events = parser.to_aggregate_multiplatform_s2s_events()
        sender = AggregateMultiplatformServerToServerSender(
            events, self.config.api_token_env_variable, self.config.s2s_token)
        return sender.send()

    def handle_converse_import(self, parser, type):
        data = parser.to_converse_data()
        if type == 'campaign':
            sender = ConverseCampaignSender(
                data, self.config.api_token_env_variable)
        elif type == 'ad':
            sender = ConverseAdSender(data, self.config.api_token_env_variable)
        else:
            raise ValueError(f'Invalid Converse sender type: {type}')
        return sender.send()

    def send_custom_conversions(self, data):
        sender = CustomConversionSender(
            data, self.config.api_token_env_variable)
        return sender.send()

    @staticmethod
    def send_s2s_events(events):
        sender = ServerToServerSender(events)
        return sender.send()

    def handle_parser(self, processing_entry, parser, filename):
        if self.config.import_type == 'custom_conversion_import':
            result = self.handle_custom_conversion_import(parser)
        elif self.config.import_type == 's2s':
            result = self.handle_s2s_import(parser)
        elif self.config.import_type == 'multiplatform_s2s':
            result = self.handle_multiplatform_s2s_import(parser)
        elif self.config.import_type == 'aggregate_multiplatform_s2s':
            result = self.handle_aggregate_multiplatform_s2s_import(parser)
        elif self.config.import_type == 'converse_campaign_level':
            result = self.handle_converse_import(parser, 'campaign')
        elif self.config.import_type == 'converse_ad_level':
            result = self.handle_converse_import(parser, 'ad')

        current_app.logger.info('{}/{} rows updated for {}'.format(
            result['successes'],
            int(result['successes']) + int(result['failures']),
            filename))

        processing_entry.status = 'succeeded'
        processing_entry.output_rows_generated = int(
            result['successes']) + int(result['failures'])
        processing_entry.output_rows_accepted = result.get('successes')
        processing_entry.finished_at = datetime.now()

    def validate_success(self, succeeded):
        if len(self._readers) != succeeded:
            raise SyncException('Not all files were processed successfully. {}/{} failed.'.format(
                len(self._readers) - succeeded, len(self._readers)))

    def handle_readers(self):
        if len(self._readers) == 0:
            current_app.logger.info(
                'No files to sync for config {} - {}'.format(
                    self.config.id, self.config.customer))
        new_md5s = [x[1] for x in self._readers]
        old_processing_entries = ProcessingEntry.get_old_processing_entries_by_config_and_md5(
            self.config.id, new_md5s)
        handled_md5s = [entry.file_md5 for entry in old_processing_entries]
        succeeded = 0
        for reader, md5, filename in self._readers:
            if md5 in handled_md5s:
                current_app.logger.info(
                    '{} - {} was already processed, skipping...'.format(filename, md5))
                succeeded += 1
                continue
            else:
                processing_entry = ProcessingEntry(
                    config_id=self.config.id,
                    status='started',
                    file_url=filename,
                    file_md5=md5,
                    started_at=datetime.now()
                )
                db.session.add(processing_entry)
                db.session.commit()

                try:
                    parser_class = self.config.get_parser_class()
                    parser = parser_class(reader)
                    self.handle_parser(processing_entry, parser, filename)
                    succeeded += 1
                except Exception as e:
                    processing_entry.status = 'failed'
                    processing_entry.finished_at = datetime.now()
                    current_app.logger.exception(
                        f'Processing failed for file {filename}',
                        extra={'error': e}
                    )
                finally:
                    db.session.commit()

        self.validate_success(succeeded)
