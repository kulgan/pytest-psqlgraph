import os

import pytest


pytest_plugins = 'pytester'


@pytest.fixture(scope="session")
def pg_config():
    return {
        "pg_driver": {
            "host": os.getenv("PG_HOST", "localhost"),
            "user": os.getenv("PG_USER", "test"),
            "password": os.getenv("PG_PASS", "test"),
            "database": os.getenv("PG_NAME", "postgres"),
        },
        "pgx_driver": {
            "host": os.getenv("PG_HOST", "localhost"),
            "user": os.getenv("PG_USER", "test"),
            "password": os.getenv("PG_PASS", "test"),
            "database": os.getenv("PG_NAME", "postgres"),
        }
    }
