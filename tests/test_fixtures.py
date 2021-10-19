import uuid

import psqlgraph
import pytest

from tests import models


@pytest.fixture
def init_data(pg_driver: psqlgraph.PsqlGraphDriver) -> None:

    with pg_driver.session_scope() as s:
        # create mother entry
        mother = models.Mother(node_id=str(uuid.uuid4()), name="Hassler M. E.")
        s.add(mother)


@pytest.fixture
def update_data(pg_driver: psqlgraph.PsqlGraphDriver) -> None:

    with pg_driver.session_scope() as s:
        # create mother entry
        mother = models.Mother(node_id=str(uuid.uuid4()), name="Springs E.")
        s.add(mother)


@pytest.fixture()
def nested_data_fixture(init_data, update_data) -> None:
    pass


@pytest.mark.parametrize("key, expectation", [(1, 1), (2, 2)])
def test_fixtures_injected(
    pg_driver: psqlgraph.PsqlGraphDriver,
    pgx_driver: psqlgraph.PsqlGraphDriver,
    key: int,
    expectation: int,
) -> None:
    assert pg_driver and pgx_driver
    assert key == expectation


@pytest.mark.usefixtures("nested_data_fixture")
@pytest.mark.parametrize("dry_run", [True, False])
def test_query(pg_driver: psqlgraph.PsqlGraphDriver, dry_run: bool) -> None:
    """Tests fixture gets initialized correctly

    Tables are created and persistence happens
    """
    assert dry_run is not None
    with pg_driver.session_scope():
        x = pg_driver.nodes(models.Mother).all()
        assert 2 == len(x)
        mom = x[0]
        assert mom.name == "Hassler M. E."
