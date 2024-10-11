import pytest
from app.models import ProcessingConfig
from app.parsers.visualiq import VisualIqParser


@pytest.fixture(autouse=True)
def delete_all_from_db(db):
    db.session.query(ProcessingConfig).delete()
    db.session.commit()
    yield


def test_get_parser_class_from_config():
    processing_config = ProcessingConfig(
        file_url="test",
        customer="foo",
        import_type="custom_conversion_import",
        parser_class="VisualIqParser"
    )

    parser_class = processing_config.get_parser_class()
    assert isinstance(parser_class(None), VisualIqParser)


def test_get_parser_class_raises_when_parser_is_not_defined():
    processing_config = ProcessingConfig(
        file_url="test",
        customer="foo",
        import_type="custom_conversion_import",
        parser_class="Test"
    )
    with pytest.raises(NotImplementedError) as e:
        processing_config.get_parser_class()
    assert 'Parser Test is not implemented' in e.value.args[0]


def test_processing_config_check_subdirs_default(db):
    processing_config = ProcessingConfig(
        file_url="test",
        customer="foo",
        import_type="custom_conversion_import",
        parser_class="VisualIqParser"
    )
    db.session.add(processing_config)
    db.session.commit()
    configs = ProcessingConfig.query.all()
    assert len(configs) == 1  # Make sure db has been emptied
    assert configs[0].check_subdirs is False
