""" Helper functions """
import logging
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import attr
import psqlgml
from psqlgraph import Node, PsqlGraphDriver, mocks

from pytest_psqlgraph.typings import Literal

from . import models

logger = logging.getLogger(__name__)


def truncate_tables(pg_driver: PsqlGraphDriver) -> None:
    """Truncates all entries in the database

    Args:
        pg_driver: active driver
    """
    with pg_driver.engine.begin() as conn:
        for table in reversed(pg_driver.engine.table_names()):
            try:
                conn.execute("delete from {} cascade".format(table))
                logger.debug(f"truncated {table}")
            except Exception as e:
                logger.warning(f"error while truncating {table} - {str(e)}", exc_info=True)


def create_tables(driver: models.DatabaseDriver) -> None:

    # create default graph tables
    driver.create_all()

    # create extra base tables
    for extra in driver.extra_bases:
        extra.metadata.create_all(driver.g.engine)


def drop_tables(driver: models.DatabaseDriver) -> None:
    """Drops all tables in the listed orm_bases"""
    driver.drop_all()

    # drop all base tables
    for base in driver.extra_bases:
        base.metadata.drop_all(driver.g.engine)


@attr.s(auto_attribs=True)
class DatabaseFixture:
    name: str
    driver: models.DatabaseDriver
    volatile: bool = False

    def pre_test(self) -> PsqlGraphDriver:
        logger.debug("Running pre test setup for {}".format(self.name))
        truncate_tables(self.driver.g)
        return self.driver.g

    def post_test(self) -> None:
        logger.debug("Running post test clean up for {}".format(self.name))
        truncate_tables(self.driver.g)

    def pre_config(self) -> None:
        logger.debug("Setting up database for {}".format(self.name))
        create_tables(self.driver)

    def post_config(self) -> None:
        logger.debug("Destroying database for {}".format(self.name))
        drop_tables(self.driver)


@attr.s(auto_attribs=True)
class DataFactory:

    model: models.DataModel
    pg_driver: PsqlGraphDriver
    dictionary: Optional[models.Dictionary]
    extension: models.MarkExtension
    globals: Optional[Dict[str, Any]]

    factory: mocks.GraphFactory = None
    mock_data: List[Node] = attr.ib(factory=list)

    def __attrs_post_init__(self) -> None:
        self.factory = mocks.GraphFactory(
            models=self.model,
            dictionary=self.dictionary,
            graph_globals=self.globals or {},
        )

    def from_source(
        self,
        source_data: psqlgml.GmlData,
    ) -> List[Node]:
        # do post processing
        nodes_cache: Dict[str, psqlgml.GmlNode] = {}
        unique_key: Literal["node_id", "submitter_id"] = source_data.get(
            "unique_field", "submitter_id"
        )
        mock_all_props = source_data.get("mock_all_props", True)
        for n in source_data["nodes"]:
            nodes_cache[n[unique_key]] = n
        self.mock_data = self.factory.create_from_nodes_and_edges(
            unique_key=unique_key,
            all_props=mock_all_props,
            nodes=source_data["nodes"],
            edges=source_data["edges"],
        )
        self.extension.pre(self.mock_data)
        with self.pg_driver.session_scope(can_inherit=False) as s:
            for node in self.mock_data:
                self.extension.run(node)
                s.add(node)
        self.extension.post(self.mock_data)
        return self.mock_data

    def clean(self) -> None:
        with self.pg_driver.session_scope() as sxn:
            for node in self.mock_data:
                node = self.pg_driver.nodes().get(node.node_id)
                if node:
                    sxn.delete(node)


@attr.s(auto_attribs=True)
class MarkHandler:

    mark: models.PsqlgraphDataMark
    fixture: DatabaseFixture

    factory: DataFactory = attr.ib(default=None)

    def __attrs_post_init__(self) -> None:
        cls = self.mark.get("extension", models.MarkExtension)
        self.factory = DataFactory(
            pg_driver=self.driver.g,
            model=self.driver.model,
            globals=self.driver.globals,
            dictionary=self.driver.dictionary,
            extension=cls(g=self.driver.g),
        )

    @property
    def driver(self) -> models.DatabaseDriver:
        return self.fixture.driver

    def pre(self) -> List[Node]:

        resource = self.mark["resource"]
        if isinstance(resource, dict):
            if validate_resource(resource, self.driver.dictionary):
                raise ValueError("Data Error")
            return self.factory.from_source(resource)

        data_dir = self.mark["data_dir"]
        source_data = psqlgml.load_resource(data_dir, resource)
        # do validation
        if validate_file_resource(resource, data_dir, self.driver.dictionary):
            raise ValueError("Invalid data specified")
        return self.factory.from_source(source_data)

    def post(self) -> None:
        self.factory.clean()


def read_schema(
    dictionary: models.Dictionary,
) -> Tuple[psqlgml.Dictionary, psqlgml.GmlSchema]:
    dictionary_name = f"{dictionary.__module__}.{dictionary.__class__.__name__}"
    di = psqlgml.from_object(dictionary.schema, name=dictionary_name, version="0.1")
    psqlgml.generate(di)
    return di, psqlgml.read_schema(dictionary_name, version="0.1")


def validate_file_resource(
    data_file: str, data_dir: str, dictionary: models.Dictionary
) -> Set[psqlgml.DataViolation]:
    di, schema = read_schema(dictionary)
    req = psqlgml.ValidationRequest(
        data_file=data_file, data_dir=data_dir, schema=schema, dictionary=di
    )
    grouped_violations = psqlgml.validate(req, print_error=True)
    violations: Set[psqlgml.DataViolation] = set.union(*grouped_violations.values())
    return violations


def validate_resource(
    resource: psqlgml.GmlData, dictionary: models.Dictionary
) -> Set[psqlgml.DataViolation]:
    di, schema = read_schema(dictionary)
    req = psqlgml.ValidationRequest("", "", schema, di, payload={"": resource})
    grouped_violations = psqlgml.validate(req, print_error=True)
    violations: Set[psqlgml.DataViolation] = set.union(*grouped_violations.values())
    return violations
