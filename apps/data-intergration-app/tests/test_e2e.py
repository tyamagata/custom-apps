import pytest
import responses
import os
from datetime import datetime, timedelta
from app.models import ProcessingConfig, ProcessingEntry
from app.sync import SyncProcessor
from io import BytesIO
from tests.boto3_mocks import BotoResourceMock


@pytest.fixture
def config():
    return ProcessingConfig(
        file_url='sftp://sftp',
        connection_username='foo',
        connection_password='pass',
        customer='foo',
        import_type='s2s',
        parser_class='ExampleServerToServerParser',
        last_successfully_processed_at=None,
    )


@responses.activate
def test_trigger_sync(db, client, app, config):
    responses.add(
        responses.GET,
        '[FILL ME IN S2S ENDPOINT]',
        status=200,
        match_querystring=False,
    )

    db.session.add(config)
    db.session.commit()

    sync_processor = SyncProcessor(config)
    sync_processor.run_sync()

    processing_entries = ProcessingEntry.query.filter_by(config_id=config.id)
    assert processing_entries.count() == 2
    for entry in processing_entries:
        assert entry.file_url in ['s2s_conversions.csv', 's2s_conversions.csv.gz']
        assert entry.status == 'succeeded'
        assert entry.output_rows_generated == 4
        assert entry.output_rows_accepted == 4
    assert len(responses.calls) == 8


@responses.activate
def test_trigger_sync_folder(db, client, app, config):
    config.check_subdirs = True
    responses.add(
        responses.GET,
        '[FILL ME IN S2S ENDPOINT]',
        status=200,
        match_querystring=False)

    db.session.add(config)
    db.session.commit()

    sync_processor = SyncProcessor(config)
    sync_processor.run_sync()

    processing_entries = ProcessingEntry.query.filter_by(config_id=config.id)
    assert processing_entries.count() == 3
    for entry in processing_entries:
        assert entry.file_url in [
            's2s_conversions.csv',
            's2s_conversions.csv.gz',
            's2s_conversions_2.csv',
        ]
        assert entry.status == 'succeeded'
        assert entry.output_rows_generated == 4
        assert entry.output_rows_accepted == 4
    assert len(responses.calls) == 12


@responses.activate
def test_trigger_sync_with_old_file(db, client, app):
    responses.add(
        responses.GET,
        '[FILL ME IN S2S ENDPOINT]',
        status=200,
        match_querystring=False)

    config = ProcessingConfig(
        file_url='sftp://sftp',
        connection_username='foo',
        connection_password='pass',
        customer='foo',
        import_type='s2s',
        parser_class='ExampleServerToServerParser',
        last_successfully_processed_at=datetime.utcnow(),
    )
    db.session.add(config)
    db.session.commit()

    sync_processor = SyncProcessor(config)
    sync_processor.run_sync()

    processing_entries = ProcessingEntry.query.filter_by(
        config_id=config.id).all()
    assert len(processing_entries) == 0
    assert len(responses.calls) == 0


def test_delete_processing_entries_when_config_deleted(db, client, app, config):
    config2 = ProcessingConfig(
        file_url='sftp://sftp',
        connection_username='foo',
        connection_password='pass',
        customer='foo',
        import_type='s2s',
        parser_class='ExampleServerToServerParser',
        last_successfully_processed_at=None
    )
    db.session.add(config)
    db.session.add(config2)
    db.session.commit()

    for _ in range(10):
        entry = ProcessingEntry(
            config_id=config.id,
            status='succeeded',
            file_url='https://example.com/conversions.csv',
            file_md5='md5'
        )
        db.session.add(entry)
    entry2 = ProcessingEntry(
        config_id=config2.id,
        status='succeeded',
        file_url='https://example.com/conversions.csv',
        file_md5='md5'
    )
    db.session.add(entry2)
    db.session.commit()

    processing_entries = ProcessingEntry.query.all()
    assert len(processing_entries) == 11

    db.session.delete(ProcessingConfig.query.first())
    db.session.commit()
    processing_entries = ProcessingEntry.query.all()
    assert len(processing_entries) == 1


def test_processing_entry_cleanup(db, client, app, config):
    db.session.add(config)
    db.session.commit()
    for days_ago in [180, 150, 120, 90, 60, 30]:
        entry = ProcessingEntry(
            config_id=config.id,
            status='succeeded',
            file_url='https://example.com/conversions.csv',
            file_md5='md5',
            started_at=datetime.utcnow() - timedelta(days=days_ago)
        )
        db.session.add(entry)
    db.session.commit()

    processing_entries = ProcessingEntry.query.all()
    assert len(processing_entries) == 6

    response = client.get('/processing_entry_cleanup')
    assert b'Deleted old entries.' == response.data
    processing_entries = ProcessingEntry.query.all()
    assert len(processing_entries) == 2


@pytest.fixture
def example_s3_file_bytes():
    with open('tests/fixtures/s3_dummy_example.csv', 'rb') as f:
        return f.read()


@responses.activate
def test_trigger_sync_with_s3_file(db, client, app, mocker, example_s3_file_bytes):
    responses.add(
        responses.GET,
        '[FILL ME IN S2S ENDPOINT]',
        status=200,
        match_querystring=False,
    )

    config = ProcessingConfig(
        file_url='s3://example/rover example s2s.csv',
        connection_username='AWS_ACCESS_KEY:AWS_SECRET',
        customer='foo',
        import_type='s2s',
        parser_class='ExampleServerToServerParser',
        last_successfully_processed_at=datetime.utcnow() - timedelta(days=20),
    )

    mocker.patch('boto3.resource', BotoResourceMock)
    mocker.patch(
        'app.s3.download_file_from_s3', return_value=BytesIO(example_s3_file_bytes)
    )

    db.session.add(config)
    db.session.commit()

    sync_processor = SyncProcessor(config)
    sync_processor.run_sync()

    processing_entries = ProcessingEntry.query.filter_by(config_id=config.id)

    assert processing_entries.count() == 1
    for entry in processing_entries:
        assert entry.file_url in ['tc-rover-s3-test/rover example s2s.csv']
        assert entry.status == 'succeeded'
        assert entry.output_rows_generated == 4
        assert entry.output_rows_accepted == 4
    assert len(responses.calls) == 4


@responses.activate
def test_trigger_sync_field_mapping_multiplatform_s2s(db, client, app):
    os.environ['new_s2s_token_for_client_x'] = 'foo'
    config = ProcessingConfig(
        file_url='sftp://sftp',
        connection_username='foo',
        connection_password='pass',
        customer='foo',
        import_type='multiplatform_s2s',
        parser_class='GenericS2SParser',
        last_successfully_processed_at=None,
        api_token_env_variable='new_s2s_token_for_client_x',
        field_mapping={
            'platform': 'Platform',
            'ad_interaction_time': 'FB click time',
            'ad_unit_id': 'FB Ad ID',
            'event_name': 'Conversion type'
        }
    )

    responses.add(
        responses.POST,
        '[FILL ME IN S2S ENDPOINT]',
        status=200,
        match_querystring=False,
        match=[responses.matchers.header_matcher({'Authorization': 'Bearer foo'})],
    )

    db.session.add(config)
    db.session.commit()

    sync_processor = SyncProcessor(config)
    sync_processor.run_sync()

    processing_entries = ProcessingEntry.query.filter_by(config_id=config.id)
    assert processing_entries.count() == 2
    for entry in processing_entries:
        assert entry.file_url in ['s2s_conversions.csv', 's2s_conversions.csv.gz']
        assert entry.status == 'succeeded'
        assert entry.output_rows_generated == 4
        assert entry.output_rows_accepted == 4
    assert len(responses.calls) == 8


@responses.activate
def test_trigger_sync_multiplatform_s2s_with_token_in_config(db, client, app):
    os.environ['new_s2s_token_for_client_x'] = 'foo'
    config = ProcessingConfig(
        file_url='sftp://sftp',
        connection_username='foo',
        connection_password='pass',
        customer='foo',
        import_type='multiplatform_s2s',
        parser_class='GenericS2SParser',
        last_successfully_processed_at=None,
        s2s_token='encrypted_s2s_token',
        field_mapping={
            'platform': 'Platform',
            'ad_interaction_time': 'FB click time',
            'ad_unit_id': 'FB Ad ID',
            'event_name': 'Conversion type'
        }
    )

    responses.add(
        responses.POST,
        '[FILL ME IN S2S ENDPOINT]',
        status=200,
        match_querystring=False,
        match=[responses.matchers.header_matcher({'Authorization': 'Bearer s2s_token'})],
    )

    db.session.add(config)
    db.session.commit()

    sync_processor = SyncProcessor(config)
    sync_processor.run_sync()

    processing_entries = ProcessingEntry.query.filter_by(config_id=config.id)
    assert processing_entries.count() == 2
    for entry in processing_entries:
        assert entry.file_url in ['s2s_conversions.csv', 's2s_conversions.csv.gz']
        assert entry.status == 'succeeded'
        assert entry.output_rows_generated == 4
        assert entry.output_rows_accepted == 4
    assert len(responses.calls) == 8
