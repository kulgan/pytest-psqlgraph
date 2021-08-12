from typing import List

import pkg_resources
import psqlgraph
import pytest

from pytest_psqlgraph.models import SchemaData

here = pkg_resources.resource_filename("tests", "data")


def append_mr(node: psqlgraph.Node) -> None:
    """Appends Mr. to father's name"""
    node.name = "Mr. {}".format(node.name)


@pytest.mark.psqlgraph_data(
    name="pg_data",
    driver_name="pg_driver",
    data_dir=here,
    resource="sample.yaml",
    unique_key="node_id",
    mock_all_props=True,
    post_processors=[append_mr],
)
def test_pgdata_with_yaml(
    pg_driver: psqlgraph.PsqlGraphDriver, pg_data: List[psqlgraph.Node]
):
    """Tests use of pgdata to load initial from yaml/json"""

    assert len(pg_data) == 3
    with pg_driver.session_scope():
        node = pg_driver.nodes().get("father-1")
        assert node.name == "Mr. Samson O."


@pytest.mark.psqlgraph_data(
    name="pg_data",
    driver_name="pg_driver",
    data_dir=here,
    resource="sample.json",
    unique_key="node_id",
    mock_all_props=True,
    post_processors=[append_mr],
)
def test_pgdata_with_json(
    pg_driver: psqlgraph.PsqlGraphDriver, pg_data: List[psqlgraph.Node]
) -> None:
    """Tests use of pgdata to load initial from yaml/json"""

    assert len(pg_data) == 3
    with pg_driver.session_scope():
        node = pg_driver.nodes().get("father-1")
        assert node.name == "Mr. Samson O."


GRAPH = SchemaData(
    nodes=[
        dict(label="mother", name="Dana O.", node_id="dana-1"),
        dict(label="son", name="Son O Dana", node_id="sn-1"),
    ],
    edges=[dict(src="dana-1", dst="sn-1", label="sons")],
)


@pytest.mark.psqlgraph_data(
    name="pgdata",
    driver_name="pg_driver",
    resource=GRAPH,
    unique_key="node_id",
    mock_all_props=True,
)
def test_pgdata_with_object(
    pg_driver: psqlgraph.PsqlGraphDriver, pgdata: List[psqlgraph.Node]
):
    assert len(pgdata) == 2

    with pg_driver.session_scope():
        dana = pg_driver.nodes().get("dana-1")
        assert len(dana.sons) == 1
