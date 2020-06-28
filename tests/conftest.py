import pytest


pytest_plugins = 'pytester'


@pytest.fixture(scope="session")
def pg_config():
    return {
        "driver_a": {
            "host": "localhost",
            "user": "test",
            "password": "test",
            "database": "dev_gdc",
        }
    }
