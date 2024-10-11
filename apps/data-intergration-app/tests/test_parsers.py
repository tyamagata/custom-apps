import json
import pytest
from app.helpers import get_csv_reader
from app.parsers.generic_s2s_parser import GenericS2SParser, FieldMissingException


from decimal import Decimal


def test_generic_custom_conversion_parser_custom_conversions():
    with open('tests/fixtures/generic_custom_conversion_example.csv') as empty_file:
        csv_data = empty_file.read().splitlines()

    with open('tests/fixtures/generic_custom_conversion_expected.json') as f:
        expected_data_custom_conversions = json.load(f)

    field_mapping_with_two_and_liquid = [
        {
            'ad_id': 'Ad ID',
            'type': 'activate_with_partner_or_follower_unique_users',
            'date': 'Install Day',
            'actions': 'Unique Users - activate_with_partner_or_follower'
        },
        {
            'ad_id': 'Ad ID',
            'type': 'complete_registration_unique_users',
            'date': 'Install Day',
            'actions': {'column_name': 'Unique Users - af_complete_registration',
                        'template': '{{ value | times: 2 }}'},
        }]

    reader = get_csv_reader(csv_data)
    parser = GenericCustomConversionParser(reader)
    parser_data = parser.to_custom_conversions(field_mapping_with_two_and_liquid)

    assert len(parser_data) == 42
    assert parser_data == expected_data_custom_conversions


def test_generic_custom_conversion_parser_liquid():
    with open('tests/fixtures/generic_custom_conversion_liquid.csv') as file:
        csv_data = file.read().splitlines()

    reader = get_csv_reader(csv_data)
    parser = GenericCustomConversionParser(reader)  # Reader can only be iterated through once so using list

    field_mapping = {
        'ad_id': 'Ad ID',
        'type': 'event1',
        'date': 'date1',
        'actions': 'action1',
        'value': {'column_name': 'value1', 'template': '{{value | plus: 5}}'}
    }
    custom_conversion_data = parser.to_custom_conversions(field_mapping)

    assert len(custom_conversion_data) == 2
    assert custom_conversion_data == [
        {
            "ad_id": "6286605046742",
            "type": "event1",
            "date": "2022-06-07",
            "actions": 0.0,
            "value": 205.55
        },
        {
            "ad_id": "6282521410342",
            "type": "event1",
            "date": "2022-06-07",
            "actions": 8.0,
            "value": 6.02
        }
        ]



def test_generic_s2s_parser():
    with open('tests/fixtures/generic_s2s_example.csv') as file:
        csv_data = file.read().splitlines()

    reader = get_csv_reader(csv_data)
    parser = GenericS2SParser(reader)
    s2s_data = parser.to_multiplatform_s2s_events()
    assert len(s2s_data) == 2
    assert s2s_data == [
        {
            'ad_unit_id': '123',
            'platform': 'facebook',
            'event_name': 'FB Conversion 1',
            'ad_interaction_time': 1559174400,
            'install_time': 1559174401,
            'event_time': 1559174402,
            'conversions': Decimal(1),
            'value': Decimal(100),
            'value_currency': 'USD'
        },
        {
            'ad_unit_id': 'abc',
            'platform': 'snapchat',
            'event_name': 'Snapchat Conversion 1',
            'ad_interaction_time': 1559174500,
            'install_time': 1559174501,
            'event_time': 1559174502,
            'conversions': Decimal(2),
            'value': Decimal(200),
            'value_currency': 'EUR'
        }
    ]


def test_generic_s2s_parser_with_field_mapping_hipto():
    with open('tests/fixtures/hiptos_source.csv') as file:
        csv_data = file.read().splitlines()

    reader = get_csv_reader(csv_data)
    parser = GenericS2SParser(reader)
    s2s_data = parser.to_multiplatform_s2s_events(field_mapping={
        'ad_unit_id': 'utm_content	',
        'event_name': 'event_name',
        'platform': '',
        'ad_interaction_time': 'timestamp	'
    })
    assert len(s2s_data) == 3
    assert s2s_data == [
        {
            'ad_unit_id': 'adid1',
            'platform': 'facebook',
            'event_name': 'Lead',
            'ad_interaction_time': 1648459448
        },
        {
            'ad_unit_id': 'adid2',
            'platform': 'facebook',
            'event_name': 'Lead',
            'ad_interaction_time': 1648461465
        },
        {
            'ad_unit_id': 'adid3',
            'platform': 'facebook',
            'event_name': 'Lead',
            'ad_interaction_time': 1648473188
        }]

    with open('tests/fixtures/generic_s2s_example_field_mapping.csv') as file:
        csv_data = file.read().splitlines()

    reader = get_csv_reader(csv_data)
    parser = GenericS2SParser(reader)
    s2s_data = parser.to_multiplatform_s2s_events(field_mapping={
        'ad_unit_id': 'ad_id',
        'platform': 'pf',
        'event_name': 'name',
        'ad_interaction_time': 'interaction_time',
        'install_time': 'i_time',
        'event_time': 'e_time',
        'conversions': 'purchases',
        'value': 'revenue',
        'value_currency': 'currency'
    })
    assert len(s2s_data) == 2
    assert s2s_data == [
        {
            'ad_unit_id': '123',
            'platform': 'facebook',
            'event_name': 'FB Conversion 1',
            'ad_interaction_time': 1559174400,
            'install_time': 1559174401,
            'event_time': 1559174402,
            'conversions': Decimal(1),
            'value': Decimal(100),
            'value_currency': 'USD'
        },
        {
            'ad_unit_id': 'abc',
            'platform': 'snapchat',
            'event_name': 'Snapchat Conversion 1',
            'ad_interaction_time': 1559174500,
            'install_time': 1559174501,
            'event_time': 1559174502,
            'conversions': Decimal(2),
            'value': Decimal(200),
            'value_currency': 'EUR'
        }
    ]


def test_generic_s2s_parser_with_partial_field_mapping():
    with open('tests/fixtures/generic_s2s_example_field_mapping.csv') as file:
        csv_data = file.read().splitlines()

    reader = get_csv_reader(csv_data)
    parser = GenericS2SParser(reader)
    s2s_data = parser.to_multiplatform_s2s_events(field_mapping={
        'ad_unit_id': 'ad_id',
        'platform': 'pf',
        'event_name': 'name',
        'ad_interaction_time': 'interaction_time'
    })
    assert len(s2s_data) == 2
    assert s2s_data == [
        {
            'ad_unit_id': '123',
            'platform': 'facebook',
            'event_name': 'FB Conversion 1',
            'ad_interaction_time': 1559174400
        },
        {
            'ad_unit_id': 'abc',
            'platform': 'snapchat',
            'event_name': 'Snapchat Conversion 1',
            'ad_interaction_time': 1559174500
        }
    ]


def test_generic_s2s_parser_with_invalid_field_mapping():
    with open('tests/fixtures/generic_s2s_example_field_mapping.csv') as file:
        csv_data = file.read().splitlines()

    reader = get_csv_reader(csv_data)
    parser = GenericS2SParser(reader)
    with pytest.raises(FieldMissingException) as e:
        parser.to_multiplatform_s2s_events({
            'ad_unit_id': 'ad_unit_id',
            'platform': 'platform',
            'event_name': 'event_name'
        })
    assert str(e.value) == "Required field(s): ad_interaction_time not found in field_mapping_s2s."

    with pytest.raises(FieldMissingException) as e:
        parser.to_multiplatform_s2s_events({
            'ad_unit_id': 'ad_unit_id',
            'event_name': 'event_name',
            'ad_interaction_time': 'ad_inteaction_time'
        })
    assert str(e.value) == "Required field(s): platform not found in field_mapping_s2s."

    with pytest.raises(FieldMissingException) as e:
        parser.to_multiplatform_s2s_events({
            'platform': 'platform',
            'event_name': 'event_name',
            'ad_interaction_time': 'ad_inteaction_time'
        })
    assert str(e.value) == "Required field(s): ad_unit_id not found in field_mapping_s2s."

    with pytest.raises(FieldMissingException) as e:
        parser.to_multiplatform_s2s_events({
            'ad_unit_id': 'ad_unit_id',
            'platform': 'platform',
            'ad_interaction_time': 'ad_inteaction_time'
        })
    assert str(e.value) == "Required field(s): event_name not found in field_mapping_s2s."

    with pytest.raises(FieldMissingException) as e:
        parser.to_multiplatform_s2s_events({})
    assert str(e.value) == "Required field(s): ad_interaction_time, \
ad_unit_id, event_name, platform not found in field_mapping_s2s."


def test_generic_s2s_parser_with_events_missing_required_values():
    with open('tests/fixtures/generic_s2s_example_missing_required_values.csv') as file:
        csv_data = file.read().splitlines()

    reader = get_csv_reader(csv_data)
    parser = GenericS2SParser(reader)
    with pytest.raises(FieldMissingException) as e:
        parser.to_multiplatform_s2s_events()
    assert str(e.value) == "Required field(s): ad_unit_id not found in event_s2s."


def test_generic_s2s_parser_with_field_mapping_using_liquid():
    with open('tests/fixtures/generic_s2s_example_date_liquid.csv') as file:
        csv_data = file.read().splitlines()

    reader = get_csv_reader(csv_data)
    parser = GenericS2SParser(list(reader))  # Reader can only be iterated through once so using list

    field_mapping = {
        'ad_unit_id': 'FB Ad ID',
        'event_name': 'Conversion type',
        'platform': None,
        'ad_interaction_time': 'FB click time',
        'event_time': 'Event time',
        'conversions': 'Actions',
        'value': 'Revenue'
    }
    field_mapping_with_liquid = {
        **field_mapping,
        'conversions': {'column_name': 'Actions', 'template': '{{ value | times: 2 }}'},
        'value': {'column_name': 'Revenue', 'template': '{{ value | plus: 0.00 | divided_by: 100 }}'}
    }
    s2s_data = parser.to_multiplatform_s2s_events(field_mapping)
    s2s_data_with_liquid = parser.to_multiplatform_s2s_events(field_mapping_with_liquid)
    assert len(s2s_data) == 4
    assert len(s2s_data_with_liquid) == 4
    assert s2s_data[0] == {
                'ad_unit_id': '123456789',
                'platform': 'facebook',
                'event_name': 'test',
                'ad_interaction_time': 1553241506,
                'event_time': 1650428400,
                'conversions': 2,
                'value': 523
            }
    assert s2s_data_with_liquid[0] == {
                'ad_unit_id': '123456789',
                'platform': 'facebook',
                'event_name': 'test',
                'ad_interaction_time': 1553241506,
                'event_time': 1650428400,
                'conversions': 4,
                'value': 5.23
            }


def test_generic_custom_conversion_parser():
    with open('tests/fixtures/generic_custom_conversion_example.csv') as file:
        csv_data = file.read().splitlines()

    reader = get_csv_reader(csv_data)
    parser = GenericCustomConversionParser(list(reader))

    field_mapping_with_one = {
        'ad_id': 'Ad ID',
        'type': 'activate_with_partner_or_follower_unique_users',
        'date': 'Install Day',
        'actions': 'Unique Users - activate_with_partner_or_follower'
        }

    field_mapping_with_one_and_liquid = {
        'ad_id': 'Ad ID',
        'type': 'activate_with_partner_or_follower_unique_users',
        'date': 'Install Day',
        'actions': {'column_name': 'Unique Users - af_complete_registration', 'template': '{{ value | times: 2 }}'},
    }

    field_mapping_with_two_and_liquid = [
        {
            'ad_id': 'Ad ID',
            'type': 'activate_with_partner_or_follower_unique_users',
            'event_name': 'activate_with_partner_or_follower_unique_users',
            'date': 'Install Day',
            'actions': 'Unique Users - activate_with_partner_or_follower'
        },
        {
            'ad_id': 'Ad ID',
            'type': 'complete_registration_unique_users',
            'date': 'Install Day',
            'actions': {'column_name': 'Unique Users - af_complete_registration',
                        'template': '{{ value | times: 2 }}'},
        }]

    cc_data_field_mapping_with_one = parser.to_custom_conversions(field_mapping_with_one)
    cc_data_field_mapping_with_one_and_liquid = parser.to_custom_conversions(field_mapping_with_one_and_liquid)
    cc_data_field_mapping_with_two_and_liquid = parser.to_custom_conversions(field_mapping_with_two_and_liquid)

    assert len(cc_data_field_mapping_with_one) == 21
    assert len(cc_data_field_mapping_with_one_and_liquid) == 21
    assert len(cc_data_field_mapping_with_two_and_liquid) == 42


def test_generic_s2s_parser_dates_convert_to_timestamp():
    with open('tests/fixtures/generic_s2s_example_date_liquid.csv') as file:
        csv_data = file.read().splitlines()

    reader = get_csv_reader(csv_data)
    parser = GenericS2SParser(reader)  # Reader can only be iterated through once so using list

    field_mapping = {
        'ad_unit_id': 'FB Ad ID',
        'event_name': 'Conversion type',
        'platform': None,
        'ad_interaction_time': 'FB click time',
        'event_time': 'Event time',
        'install_time': 'Install time',
        'conversions': 'Actions',
        'value': 'Revenue'
    }
    s2s_data = parser.to_multiplatform_s2s_events(field_mapping)
    assert len(s2s_data) == 4
    assert s2s_data[0] == {
        'ad_unit_id': '123456789',
        'platform': 'facebook',
        'event_name': 'test',
        'ad_interaction_time': 1553241506,
        'event_time': 1650428400,
        'install_time': 1650428400,
        'conversions': 2,
        'value': 523
    }
