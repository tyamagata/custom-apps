class DictType():
    FIELD_MAPPING_S2S = 'field_mapping_s2s'
    FIELD_MAPPING_CUSTOM_CONVERSION = 'field_mapping_custom_conversion'
    EVENT_S2S = 'event_s2s'
    EVENT_CUSTOM_CONVERSION = 'event_custom_conversion'
    LIQUID = 'liquid'


REQUIRED_FIELDS_MAPPING = {
    DictType.FIELD_MAPPING_S2S: ['ad_unit_id', 'platform', 'event_name', 'ad_interaction_time'],
    DictType.FIELD_MAPPING_CUSTOM_CONVERSION: ['ad_id', 'type', 'date', 'actions'],
    DictType.EVENT_S2S: ['ad_unit_id', 'platform', 'event_name', 'ad_interaction_time'],
    DictType.EVENT_CUSTOM_CONVERSION: ['ad_id', 'type', 'date', 'actions'],
    DictType.LIQUID: ['column_name', 'template']
}


OPTIONAL_FIELDS_MAPPING = {
    DictType.FIELD_MAPPING_S2S: ['event_time', 'install_time', 'conversions', 'value', 'value_currency'],
    DictType.FIELD_MAPPING_CUSTOM_CONVERSION: ['value'],
    DictType.EVENT_S2S: ['event_time', 'install_time', 'conversions', 'value', 'value_currency'],
    DictType.EVENT_CUSTOM_CONVERSION: ['value'],
    DictType.LIQUID: ['column_name', 'template']
}
