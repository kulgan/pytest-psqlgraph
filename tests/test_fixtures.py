import uuid

import psqlgraph
import pytest

from tests import models


@pytest.fixture
def init_data(pg_driver: psqlgraph.PsqlGraphDriver) -> None:

    with pg_driver.session_scope() as s:
        # create mother entry
        mother = models.Mother(node_id=str(uuid.uuid4()), name="Isioma M. E.")
        s.add(mother)


@pytest.mark.parametrize("key, expectation", [(1, 1), (2, 2)])
def test_fixtures_injected(
    pg_driver: psqlgraph.PsqlGraphDriver,
    pgx_driver: psqlgraph.PsqlGraphDriver,
    key: int,
    expectation: int,
) -> None:
    assert pg_driver and pgx_driver
    assert key == expectation


def test_query(pg_driver: psqlgraph.PsqlGraphDriver, init_data) -> None:
    """Tests fixture gets initialized correctly

    Tables are created and persistence happens
    """

    with pg_driver.session_scope():
        x = pg_driver.nodes(models.Mother).all()
        assert 1 == len(x)
        mom = x[0]
        assert mom.name == "Isioma M. E."
