import os

import pytest
from psqlgraph.base import VoidedBase

from tests import models

pytest_plugins = "pytester"


@pytest.fixture(scope="session")
def psqlgraph_config():
    return {
        "pg_driver": {
            "host": os.getenv("PG_HOST", "localhost"),
            "user": os.getenv("PG_USER", "test"),
            "password": os.getenv("PG_PASS", "test"),
            "database": os.getenv("PG_NAME", "postgres"),
            "package_namespace": None,
            "dictionary": models.Dictionary(),
            "models": models,
            "extra_bases": [VoidedBase],
        },
        "pgx_driver": {
            "host": os.getenv("PG_HOST", "localhost"),
            "user": os.getenv("PG_USER", "test"),
            "password": os.getenv("PG_PASS", "test"),
            "database": os.getenv("PG_NAME", "postgres"),
            "dictionary": models.Dictionary(),
            "models": models,
        },
    }
