import uuid
from os import path

import pytest

import models

here = path.abspath(path.dirname(__file__))


def test_init_drivers(pg_driver, pgx_driver):
    """ Tests fixture gets initialized correctly

    Tables are created and persistence happens
    Args:
        pg_driver (psqlgraph.PsqlGraphDriver): pg driver
    """
    assert pg_driver and pgx_driver

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
        assert mom.name == "Isioma M. E."


def append_mr(node):
    """ Appends Mr. to father's name

    Args:
        node (models.Node):
    """
    node.name = "Mr. {}".format(node.name)


@pytest.mark.pgdata(
    name="pg_data",
    driver="pg_driver",
    params=dict(
        model=models,
        dictionary=models.Dictionary(),
        source="{}/data/sample.yaml".format(here),
        unique_key="node_id",
        mock_all_props=True,
        post_processors={
            "father": [append_mr]
        }
    )
)
def test_pgdata_with_yaml(pg_driver, pg_data):
    """ Tests use of pgdata to load initial from yaml/json """

    assert len(pg_data) == 3
    with pg_driver.session_scope():
        node = pg_driver.nodes().get("father-1")
        assert node.name == "Mr. Samson O."


@pytest.mark.pgdata(
    name="pg_data",
    driver="pg_driver",
    params=dict(
        model=models,
        dictionary=models.Dictionary(),
        source="{}/data/sample.json".format(here),
        unique_key="node_id",
        mock_all_props=True,
        post_processors={
            "father": [append_mr]
        }
    )
)
def test_pgdata_with_json(pg_driver, pg_data):
    """ Tests use of pgdata to load initial from yaml/json """

    assert len(pg_data) == 3
    with pg_driver.session_scope():
        node = pg_driver.nodes().get("father-1")
        assert node.name == "Mr. Samson O."


GRAPH = dict(
    nodes=[
        dict(label="mother", name="Dana O.", node_id="dana-1"),
        dict(label="son", name="Son O Dana", node_id="sn-1"),
    ],
    edges=[
        dict(src="dana-1", dst="sn-1", label="sons")
    ]
)


@pytest.mark.pgdata(
    driver="pg_driver",
    params=dict(
        model=models,
        dictionary=models.Dictionary(),
        source=GRAPH,
        unique_key="node_id",
        mock_all_props=True
    )
)
def test_pgdata_with_object(pg_driver, pgdata):
    assert len(pgdata) == 2

    with pg_driver.session_scope():
        dana = pg_driver.nodes().get("dana-1")
        assert len(dana.sons) == 1
