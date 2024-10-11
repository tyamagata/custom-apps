import datetime
from sqlalchemy.orm import validates, relationship
from sqlalchemy import or_
from flask_sqlalchemy import SQLAlchemy
from app.parsers.example_server_to_server import ExampleServerToServerParser


db = SQLAlchemy()


class BaseProcessingConfig:
    id = db.Column(db.Integer, primary_key=True)
    customer = db.Column(db.String, nullable=False)
    import_type = db.Column(db.String, nullable=False)
    api_token_env_variable = db.Column(db.String)
    last_processing_started_at = db.Column(db.DateTime)
    last_processed_at = db.Column(db.DateTime, index=True)
    last_successfully_processed_at = db.Column(db.DateTime)

    @validates('import_type')
    def validate_import_type(self, key, import_type):
        assert import_type in [
                                's2s',
                                'multiplatform_s2s',
                                'aggregate_multiplatform_s2s',
                                'custom_conversion_import',
                                'converse_campaign_level',
                                'converse_ad_level'
                            ]
        return import_type

    @classmethod
    def get_syncable_configs(cls, force=False):
        if force:
            return cls.query.all()
        else:
            ten_minutes_ago = datetime.datetime.now() - datetime.timedelta(seconds=10*60)
            return cls.query.filter(or_(cls.last_processed_at < ten_minutes_ago, cls.last_processed_at.is_(None))).all()


class ProcessingConfig(db.Model, BaseProcessingConfig):
    __tablename__ = 'processing_configs'
    file_url = db.Column(db.String, nullable=False)
    check_subdirs = db.Column(db.Boolean, default=False, server_default="f")
    connection_username = db.Column(db.String)
    connection_password = db.Column(db.String)
    connection_port = db.Column(db.Integer)
    connection_path = db.Column(db.String)
    parser_class = db.Column(db.String, nullable=False)
    field_mapping = db.Column(db.JSON, nullable=True)
    s2s_token = db.Column(db.String, nullable=True)
    processing_entries = relationship(
        'ProcessingEntry',
        backref="processing_config",
        cascade="all,delete",
        passive_deletes=True,
    )

    def __repr__(self):
        return f'ProcessingConfig (file-based): {self.id} - {self.customer}'

    def get_parser_class(self):
        if self.parser_class == 'ExampleServerToServerParser':
            return ExampleServerToServerParser
        else:
            raise NotImplementedError(
                'Parser {} is not implemented'.format(self.parser_class))


class BaseProcessingEntry:
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String, nullable=False)
    output_rows_generated = db.Column(db.Integer)
    output_rows_accepted = db.Column(db.Integer)
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)

    @validates('status')
    def validate_status(self, key, status):
        assert status in ['started', 'succeeded', 'failed']
        return status


class ProcessingEntry(db.Model, BaseProcessingEntry):
    __tablename__ = 'processing_entries'
    config_id = db.Column(
        db.ForeignKey('processing_configs.id', ondelete="CASCADE"), nullable=False, index=True
    )
    file_url = db.Column(db.String, nullable=False)
    file_md5 = db.Column(db.String, nullable=False, index=True)

    @classmethod
    def get_old_processing_entries_by_config_and_md5(cls, config_id, new_md5s):
        return cls.query.filter_by(config_id=config_id) \
            .filter(cls.status.in_(['succeeded', 'started'])) \
            .filter(cls.file_md5.in_(new_md5s)).all()
