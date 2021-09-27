import os
from typing import Dict

import pytest
from psqlgraph.base import ORMBase, VoidedBase

from pytest_psqlgraph.models import DatabaseDriverConfig
from tests import models

pytest_plugins = "pytester"


@pytest.fixture(scope="session")
def psqlgraph_config() -> Dict[str, DatabaseDriverConfig]:
    return {
        "pg_driver": DatabaseDriverConfig(
            host=os.getenv("PG_HOST", "localhost"),
            user=os.getenv("PG_USER", "test"),
            password=os.getenv("PG_PASS", "test"),
            database=os.getenv("PG_NAME", "postgres"),
            package_namespace=None,
            dictionary=models.Dictionary(),
            model=models,
            orm_base=ORMBase,
            extra_bases=[VoidedBase],
        ),
        "pgx_driver": DatabaseDriverConfig(
            host=os.getenv("PG_HOST", "localhost"),
            user=os.getenv("PG_USER", "test"),
            password=os.getenv("PG_PASS", "test"),
            database=os.getenv("PG_NAME", "postgres"),
            dictionary=models.Dictionary(),
            model=models,
        ),
    }
