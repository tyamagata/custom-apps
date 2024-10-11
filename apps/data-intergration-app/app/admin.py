import os
from urllib.parse import urlparse
from flask_admin import Admin
from redis import Redis
from flask_admin.contrib import rediscli
from flask_admin.contrib.sqla import ModelView
from app.models import ProcessingConfig, ProcessingEntry, db
from flask_admin.actions import action
from flask import flash, current_app
from app.helpers import ConfigVariableHelper
from app.dict_types import REQUIRED_FIELDS_MAPPING, OPTIONAL_FIELDS_MAPPING, DictType
from google.api_core.exceptions import InvalidArgument
from binascii import Error as Base64Error


class LiquidException(Exception):
    pass


class FieldMappingException(Exception):
    pass


class ProcessingConfigAdminView(ModelView):
    column_display_pk = True
    column_hide_backrefs = False
    column_filters = ['customer', 'import_type', 'parser_class']
    form_create_rules = (
        'file_url', 'connection_username', 'connection_password', 'connection_path', 'customer', 'import_type',
        'parser_class', 'api_token_env_variable', 'check_subdirs', 'field_mapping', 's2s_token')
    form_excluded_columns = (
        'processing_entries', 'connection_port'
    )

    @action('reset', 'Reset entries', 'Are you sure you want to reset processing entries for selected config(s)?')
    def action_reset_processing_entries(self, ids):
        try:
            processing_entries = ProcessingEntry.query.filter(ProcessingEntry.config_id.in_(ids)).all()
            for entry in processing_entries:
                db.session.delete(entry)

            processing_configs = ProcessingConfig.query.filter(ProcessingConfig.id.in_(ids)).all()
            for config in processing_configs:
                config.last_processing_started_at = None
                config.last_processed_at = None
                config.last_successfully_processed_at = None
            db.session.commit()

            flash('Entries successfully reset')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise

    def validate_liquid_dict(self, liquid_dict):
        for key, value in liquid_dict.items():
            if key not in ['template', 'column_name']:
                raise LiquidException(f'Invalid key: "{key}". Mapping needs to have two keys: column_name and template')
            if not isinstance(value, str):
                raise LiquidException('Liquid template must be a string. See docs: https://jg-rp.github.io/liquid/')

    def validate_field_mapping(self, field_mappings, dict_type):
        if field_mappings in [None, {}]:
            raise FieldMappingException("field_mapping values needed")
        if dict_type is None:
            raise FieldMappingException("import type is missing or not supported for field mapping")

        if isinstance(field_mappings, dict):
            field_mappings = [field_mappings]

        required_fields = REQUIRED_FIELDS_MAPPING[dict_type]
        optional_fields = OPTIONAL_FIELDS_MAPPING[dict_type]

        for field_mapping in field_mappings:
            missing_fields = set(required_fields) - set(field_mapping.keys())
            invalid_fields = set(field_mapping.keys()) - set(required_fields + optional_fields)
            if missing_fields:
                raise FieldMappingException(f'Missing following fields from field_mapping: {list(missing_fields)}')
            if invalid_fields:
                raise FieldMappingException(f'Field(s) not allowed: {invalid_fields}. \
                    Allowed fields: {set(required_fields + optional_fields)}')

            for key, value in field_mapping.items():
                if isinstance(value, dict):
                    self.validate_liquid_dict(value)
                elif isinstance(value, str):
                    pass
                else:
                    raise FieldMappingException(f"field_mapping values needs to be of type string or dict\
                        - key {key} is {type(value)}")
        return True

    def validate_form(self, form):
        try:
            if hasattr(form, 'field_mapping') and form.field_mapping.data not in [None, {}]:
                if form.import_type.data == 'custom_conversion_import':
                    self.validate_field_mapping(form.field_mapping.data, DictType.FIELD_MAPPING_CUSTOM_CONVERSION)
                if form.import_type.data == 'multiplatform_s2s':
                    self.validate_field_mapping(form.field_mapping.data, DictType.FIELD_MAPPING_S2S)
                if form.import_type.data == 'aggregate_multiplatform_s2s':
                    self.validate_field_mapping(form.field_mapping.data, DictType.FIELD_MAPPING_S2S)
            return super().validate_form(form)
        except LiquidException as e:
            flash(f'LiquidException: {e}')
        except FieldMappingException as e:
            flash(f'FieldMappingException: {e}')

    def on_model_change(self, form, model, is_created):
        # If S2S token exists and it's not encrypted, encrypt it with Google KMS.
        if model.s2s_token is not None:
            config_helper = ConfigVariableHelper(os.getenv('FLASK_ENV'), current_app.config.get('GOOGLE_CLOUD_PROJECT'))
            try:
                config_helper.decrypt(model.s2s_token)
            except (InvalidArgument, Base64Error):
                model.s2s_token = config_helper.encrypt(model.s2s_token)
        super().on_model_change(form, model, is_created)


class ProcessingEntryAdminView(ModelView):
    can_create = False
    column_display_pk = True
    column_filters = ['processing_config.id', 'processing_config.customer']
    form_excluded_columns = ('processing_config')


admin = Admin()
admin.add_view(ProcessingConfigAdminView(ProcessingConfig, db.session))
admin.add_view(ProcessingEntryAdminView(ProcessingEntry, db.session))

redis_url = urlparse(os.getenv('REDIS_URL'))
admin.add_view(rediscli.RedisCli(Redis(host=redis_url.hostname), name="Redis CLI"))
