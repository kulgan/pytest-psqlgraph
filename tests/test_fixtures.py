import uuid

import psqlgraph

from tests import models


def test_init_drivers(
    pg_driver: psqlgraph.PsqlGraphDriver, pgx_driver: psqlgraph.PsqlGraphDriver
) -> None:
    """Tests fixture gets initialized correctly

    Tables are created and persistence happens
    Args:
        pg_driver (psqlgraph.PsqlGraphDriver): pg driver
    """
    assert pg_driver and pgx_driver

    with pg_driver.session_scope() as s:
        x = pg_driver.nodes(models.Mother).count()
        assert 0 == x

        # create mother entry
        mother = models.Mother(node_id=str(uuid.uuid4()), name="Isioma M. E.")
        s.add(mother)

    with pg_driver.session_scope() as s:
        x = pg_driver.nodes(models.Mother).all()
        assert 1 == len(x)
        mom = x[0]
        assert mom.node_id == mother.node_id
        assert mom.name == "Isioma M. E."
