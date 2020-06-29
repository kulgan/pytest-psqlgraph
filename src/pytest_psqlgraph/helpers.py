""" Helper functions """
import json

import attr
import psqlgraph
import yaml
from psqlgraph import ext, mocks
from psqlgraph.base import ORMBase


def truncate_tables(pg_driver):
    """ Truncates all entries in the datanase

    Args:
        pg_driver (psqlgraph.PsqlGraphDriver): active driver
    """
    with pg_driver.engine.begin() as conn:
        for table in reversed(pg_driver.engine.table_names()):
            conn.execute('delete from {} cascade'.format(table))


def create_tables(pg_driver, namespace):
    base = ORMBase if namespace is None else ext.get_orm_base(namespace)
    psqlgraph.create_all(pg_driver.engine, base=base)


def drop_tables(bases, pg_driver):
    """ Drops all tables in the listed orm_bases

    Args:
        bases (list[sqlalchemy.Base):
        pg_driver (psqlgraph.PsqlGraphDriver):
    """
    for base in bases:
        base.metadata.drop_all(pg_driver.engine)


class Marks(object):

    def pgdata(self, name, params):
        """ Loads psqlgraph data from provided source

        Args:
            name (str): single string denoting the argument name to inject in to the test function
            config (dict): information on what data to load
        """


@attr.s
class FixtureHandler(object):

    driver_name = attr.ib(type=str)
    volatile = attr.ib(default=False)
    _pg_driver = attr.ib(type=psqlgraph.PsqlGraphDriver, init=False, repr=False)

    def pre(self, pg_driver):
        self._pg_driver = pg_driver
        truncate_tables(self._pg_driver)
        return pg_driver

    def post(self):
        truncate_tables(self._pg_driver)


@attr.s
class PgDataHandler(FixtureHandler):

    kwargs = attr.ib(default={})
    volatile = attr.ib(init=False, default=True)
    factory = attr.ib(init=False)

    def pre(self, pg_driver):
        self._pg_driver = pg_driver
        self.factory = DataFactory(
            pg_driver=self._pg_driver,
            models=self.kwargs.get("model"),
            defaults=self.kwargs.get("defaults"),
            dictionary=self.kwargs.get("dictionary"),
            post_processors=self.kwargs.get("post_processors")
        )

        source_file = self.kwargs.get("source")
        unique_key = self.kwargs.get("unique_key")
        mock_all_props = self.kwargs.get("mock_all_props", False)
        self.factory.from_source(source_file, unique_key, mock_all_props)
        return self.factory.mock_data

    def post(self):
        self.factory.clean()


@attr.s
class DataFactory(object):

    models = attr.ib()
    pg_driver = attr.ib()
    dictionary = attr.ib()
    post_processors = attr.ib()
    defaults = attr.ib(default={})

    factory = attr.ib(init=False)
    mock_data = attr.ib(init=False)

    def __attrs_post_init__(self):
        self.factory = mocks.GraphFactory(
            models=self.models,
            dictionary=self.dictionary,
            graph_globals=self.defaults,
        )

    def from_source(self, source_file, unique_key, mock_all_props=False):
        source_data = load_source(source_file)
        self.mock_data = self.factory.create_from_nodes_and_edges(
            unique_key=unique_key,
            all_props=mock_all_props,
            nodes=source_data["nodes"],
            edges=source_data["edges"],
        )
        # do post processing

    def clean(self):
        with self.pg_driver.session_scope() as sxn:
            for node in self.mock_data:
                node = self.pg_driver.nodes().get(node.node_id)
                if node:
                    sxn.delete(node)


def load_source(source):
    ext = source.split(".")[-1]
    if ext in ["yaml", "yml"]:
        with open(source, "r") as f:
            return yaml.safe_load(f.read())
    if ext == "json":
        with open(source, "r") as f:
            return json.load(f)
    raise ValueError("Unsupported extension {}, file must end with one of {}".format(
        ext, ["json", "yaml", "yml"]
    ))
