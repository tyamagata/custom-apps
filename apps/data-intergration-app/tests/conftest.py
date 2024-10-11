import pytest
from app import create_app
from app.models import db as _db


@pytest.fixture(scope='session', autouse=True)
def app(request):
    app = create_app(testing=True)
    with app.app_context():
        _db.init_app(app)
        yield app


@pytest.fixture(scope='session')
def client(app):
    client = app.test_client()
    yield client


@pytest.fixture(scope='function')
def db(app):
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.commit()
        _db.drop_all()
