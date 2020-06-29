import uuid
from os import path

import pytest

import models

here = path.abspath(path.dirname(__file__))


def test_initialization(pg_driver):
    """ Tests fixture gets initialized correctly

    Tables are created and persistence happens
    Args:
        pg_driver (psqlgraph.PsqlGraphDriver): pg driver
    """
    with pg_driver.session_scope() as s:
        x = pg_driver.nodes(models.Mother).count()
        assert 0 == x

        # create mother entry
        mother = models.Mother(
            node_id=str(uuid.uuid4()),
            name="Isioma M. E."
        )
        s.add(mother)

    with pg_driver.session_scope() as s:
        x = pg_driver.nodes(models.Mother).all()
        assert 1 == len(x)
        mom = x[0]
        assert mom.node_id == mother.node_id
        assert mom.name == mother.name


@pytest.mark.pgdata(
    name="pg_data",
    params=dict(
        model=models,
        dictionary=models.Dictionary(),
        source="{}/data/sample.yaml".format(here),
        unique_key="node_id",
    )
)
def test_again(pg_driver, pg_data):
    print(pg_data)
