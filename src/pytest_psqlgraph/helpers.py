""" Helper functions """
import json
import logging
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import attr
import psqlgraph
import yaml
from psqlgml import dictionary as d
from psqlgml import models as m
from psqlgml import schema as s
from psqlgml import validators as v
from psqlgraph import mocks

from . import models

logger = logging.getLogger(__name__)


def truncate_tables(pg_driver: psqlgraph.PsqlGraphDriver) -> None:
    """Truncates all entries in the datanase

    Args:
        pg_driver (psqlgraph.PsqlGraphDriver): active driver
    """
    with pg_driver.engine.begin() as conn:
        for table in reversed(pg_driver.engine.table_names()):
            conn.execute("delete from {} cascade".format(table))


def create_tables(driver: models.DatabaseDriver) -> None:

    # create default graph tables
    psqlgraph.create_all(driver.g.engine, base=driver.orm_base)

    # create extra base tables
    for extra in driver.extra_bases:
        extra.metadata.create_all(driver.g.engine)


def drop_tables(driver: models.DatabaseDriver) -> None:
    """Drops all tables in the listed orm_bases"""
    psqlgraph.base.drop_all(driver.g.engine, driver.orm_base)

    # drop all base tables
    for base in driver.extra_bases:
        base.metadata.drop_all(driver.g.engine)


@attr.s(auto_attribs=True)
class DatabaseFixture:
    name: str
    driver: models.DatabaseDriver
    volatile: bool = False

    def pre_test(self) -> psqlgraph.PsqlGraphDriver:
        logger.info("Pre test setup for {}".format(self.name))
        truncate_tables(self.driver.g)
        return self.driver.g

    def post_test(self) -> None:
        logger.info("Post test clean up for {}".format(self.name))
        truncate_tables(self.driver.g)

    def pre_config(self) -> None:
        logger.info("Setting up database for {}".format(self.name))
        create_tables(self.driver)

    def post_config(self) -> None:
        logger.info("Destroying database for {}".format(self.name))
        drop_tables(self.driver)


@attr.s(auto_attribs=True)
class DataFactory:

    model: models.DataModel
    pg_driver: psqlgraph.PsqlGraphDriver
    dictionary: Optional[models.Dictionary]
    post_processors: Iterable[models.PostProcessor]
    globals: Optional[Dict[str, Any]]

    factory: mocks.GraphFactory = None
    mock_data: List[psqlgraph.Node] = attr.ib(factory=list)

    def __attrs_post_init__(self) -> None:
        self.factory = mocks.GraphFactory(
            models=self.model,
            dictionary=self.dictionary,
            graph_globals=self.globals or {},
        )

    def from_source(
        self,
        source_data: m.SchemaData,
        unique_key: str,
        mock_all_props: bool = False,
    ) -> List[psqlgraph.Node]:
        self.mock_data = self.factory.create_from_nodes_and_edges(
            unique_key=source_data.get("unique_field", unique_key),
            all_props=mock_all_props,
            nodes=source_data["nodes"],
            edges=source_data["edges"],
        )
        # do post processing
        with self.pg_driver.session_scope() as s:
            for node in self.mock_data:
                for func in self.post_processors:
                    func(node)
                s.add(node)
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
        self.factory = DataFactory(
            pg_driver=self.driver.g,
            model=self.driver.model,
            globals=self.driver.globals,
            dictionary=self.driver.dictionary,
            post_processors=self.mark.get("post_processors") or [],
        )

    @property
    def driver(self) -> models.DatabaseDriver:
        return self.fixture.driver

    def pre(self) -> List[psqlgraph.Node]:

        unique_key = self.mark["unique_key"]
        mock_all_props = self.mark.get("mock_all_props", False)

        resource = self.mark["resource"]
        if isinstance(resource, dict):
            if validate_resource(resource, self.driver.dictionary):
                raise ValueError("Data Error")
            return self.factory.from_source(resource, unique_key, mock_all_props)

        data_dir = self.mark["data_dir"]
        source_data = load_data_files(data_dir, resource)
        # do validation
        if validate_file_resource(resource, data_dir, self.driver.dictionary):
            raise ValueError("Invalid data specified")
        return self.factory.from_source(source_data, unique_key, mock_all_props)

    def post(self) -> None:
        self.factory.clean()


def read_schema(dictionary: models.Dictionary) -> Tuple[d.Dictionary, m.GmlSchema]:
    schema = dictionary.schema
    raw: Dict[str, d.Schema] = {}
    for label, entry in schema.items():
        raw[label] = d.Schema(raw=entry)
    di = d.Dictionary(schema=raw, version="0.1", name="ineral", url="NA")
    s.generate(di)
    return di, s.read("ineral", version="0.1")


def validate_file_resource(
    data_file: str, data_dir: str, dictionary: models.Dictionary
) -> Set[v.DataViolation]:
    di, schema = read_schema(dictionary)
    req = v.ValidationRequest(
        data_file=data_file, data_dir=data_dir, schema=schema, dictionary=di
    )
    grouped_violations = v.validate(req, print_error=True)
    violations: Set[v.DataViolation] = set.union(*grouped_violations.values())
    return violations


def validate_resource(
    resource: m.SchemaData, dictionary: models.Dictionary
) -> Set[v.DataViolation]:
    di, schema = read_schema(dictionary)
    req = v.ValidationRequest("", "", schema, di, payload={"": resource})
    grouped_violations = v.validate(req, print_error=True)
    violations: Set[v.DataViolation] = set.union(*grouped_violations.values())
    return violations


def loads(file_name: str) -> m.SchemaData:
    extension = file_name.split(".")[-1]
    with open(file_name, "r") as r:
        if extension == "json":
            return json.loads(r.read())

        if extension in ["yml", "yaml"]:
            return yaml.safe_load(r)
    return m.SchemaData()


def load_data_files(resource_folder: str, resource_name: str) -> m.SchemaData:
    file_name = f"{resource_folder}/{resource_name}"
    rss: m.SchemaData = loads(file_name)

    extended_resource = rss.pop("extends", None)
    if not extended_resource:
        return rss

    extended = load_data_files(resource_folder, extended_resource)

    # merge
    rss["nodes"] += extended["nodes"]
    rss["edges"] += extended["edges"]

    if "summary" not in rss:
        rss["summary"] = extended.get("summary", {})
        return rss

    for summary in extended.get("summary", {}):
        if summary in rss["summary"]:
            rss["summary"][summary] += extended["summary"][summary]
        else:
            rss["summary"][summary] = extended["summary"][summary]

    return rss
