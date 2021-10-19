from typing import List

import pkg_resources
import psqlgraph
import pytest

from pytest_psqlgraph.models import MarkExtension

here = pkg_resources.resource_filename("tests", "data")


class AppendExtension(MarkExtension):
    def run(self, node: psqlgraph.Node) -> None:
        node.name = f"Mr. {node.name}"


@pytest.mark.psqlgraph_data(
    name="pg_data",
    driver_name="pg_driver",
    data_dir=here,
    resource="sample.yaml",
    extension=AppendExtension,
)
def test_pgdata_with_yaml(
    pg_driver: psqlgraph.PsqlGraphDriver, pg_data: List[psqlgraph.Node]
) -> None:
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
    extension=AppendExtension,
)
def test_pgdata_with_json(
    pg_driver: psqlgraph.PsqlGraphDriver, pg_data: List[psqlgraph.Node]
) -> None:
    """Tests use of pgdata to load initial from yaml/json"""

    assert len(pg_data) == 3
    with pg_driver.session_scope():
        node = pg_driver.nodes().get("father-1")
        assert node.name == "Mr. Samson O."


GRAPH = dict(
    unique_field="node_id",
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
)
def test_pgdata_with_object(pg_driver: psqlgraph.PsqlGraphDriver, pgdata: List[psqlgraph.Node]):
    assert len(pgdata) == 2

    with pg_driver.session_scope():
        dana = pg_driver.nodes().get("dana-1")
        assert len(dana.sons) == 1


@pytest.fixture()
def data_fix(pg_driver: psqlgraph.PsqlGraphDriver) -> None:

    with pg_driver.session_scope():
        dana = pg_driver.nodes().get("dana-1")
        dana.name = "Dana D. O."


@pytest.mark.psqlgraph_data(
    name="pgdata",
    driver_name="pg_driver",
    resource=GRAPH,
)
@pytest.mark.usefixtures("data_fix")
def test_with_fixture(pg_driver: psqlgraph.PsqlGraphDriver, pgdata: List[psqlgraph.Node]) -> None:
    assert len(pgdata) == 2
    with pg_driver.session_scope():
        dana = pg_driver.nodes().get("dana-1")

        assert dana.name == "Dana D. O."


@pytest.mark.psqlgraph_data(
    driver_name="pg_driver",
    resource=GRAPH,
)
@pytest.mark.usefixtures("data_fix")
def test_with_fixture__no_inject(pg_driver: psqlgraph.PsqlGraphDriver) -> None:
    with pg_driver.session_scope():
        dana = pg_driver.nodes().get("dana-1")

        assert dana.name == "Dana D. O."
