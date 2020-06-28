import json
import logging
import sys

import attr
import psqlgraph
import pytest
import yaml
from _pytest.fixtures import FixtureLookupError
from psqlgraph import mocks

from pytest_psqlgraph import helpers

logger = logging.getLogger("pytest_psqlgraph.plugin")


def pytest_addoption(parser):
    group = parser.getgroup("psqlgraph")
    group.addoption("--drop-all", action="store_true", help="drop all tables before starting")


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


@attr.s
class PsqlGraphConfig(object):
    name = attr.ib()
    bases = attr.ib()
    config = attr.ib()
    pg_driver = attr.ib(init=False, repr=False, hash=False)

    def __attrs_post_init__(self):
        self.pg_driver = psqlgraph.PsqlGraphDriver(**self.config)

    def pre(self):
        helpers.truncate_tables(self.pg_driver)
        return self.pg_driver

    def post(self):
        logger.debug("clean up in progress")
        helpers.truncate_tables(self.pg_driver)


class PsqlgraphPlugin(object):

    configs = {}

    @property
    def default_driver(self):
        if len(self.configs) == 1:
            return self.configs.keys()[0]
        return None

    def pytest_configure(self, config):
        config.addinivalue_line(
            "markers", "pgdata(driver, source, model, dictionary, defaults, unique_key, mock_all_props, "
                       "post_processors): loads data for testing "
        )

    def pytest_runtest_call(self, item):

        for marker in item.iter_markers(name="pgdata"):

            driver_name = marker.kwargs.get("driver", self.default_driver)
            cfg = self.configs[driver_name]
            factory = DataFactory(
                pg_driver=cfg.pg_driver,
                models=marker.kwargs.get("model"),
                defaults=marker.kwargs.get("defaults"),
                dictionary=marker.kwargs.get("dictionary"),
                post_processors=marker.kwargs.get("post_processors")
            )

            source_file = marker.kwargs.get("source")
            unique_key = marker.kwargs.get("unique_key")
            mock_all_props = marker.kwargs.get("mock_all_props", False)
            factory.from_source(source_file, unique_key, mock_all_props)

            item.funcargs["pg_data"] = factory.mock_data
            item.addfinalizer(factory.clean)
            sys.stdout.flush()

    @pytest.fixture(scope="session", autouse=True)
    def psqlgraph(self, pg_config):
        """ A psqlgraph driver instance

            Initializes the database tables and makes fixtures available
            Args:
                request:
                pg_config (dict[str, dict]): driver fixture name and configuration options pairs

                Example:
                    code-block::
                        {"g": {
                            "host": "localhost",
                            "user": "test",
                            "password": "test",
                            "database": "test_db",
                            "ng_bases": []
                            }
                        }

            """
        for driver_name, config in pg_config.items():
            cfg = PsqlGraphConfig(name=driver_name, bases=config.pop("ng_bases", []), config=config)
            helpers.create_tables(
                pg_driver=cfg.pg_driver,
                namespace=config.get("namespace")
            )
            # self.inject_fixture(name=driver_name, pg_driver=cfg.pg_driver)
            for base in cfg.bases:
                base.metadata.create_all(cfg.pg_driver.engine)
            self.configs[cfg.name] = cfg
        yield
        for _, cfg in self.configs.items():
            helpers.drop_tables(cfg.bases, cfg.pg_driver)

    @pytest.fixture(autouse=True)
    def inject_driver(self, request):
        """ Injects named pg_driver fixture

        Args:
            request (_pytest.fixtures.SubRequest):
        Returns:

        """
        item = request._pyfuncitem
        for arg_name in request.fixturenames:
            try:
                request.getfixturevalue(arg_name)
            except FixtureLookupError:
                if arg_name in self.configs:
                    cfg = self.configs.get(arg_name)
                    item.funcargs[arg_name] = cfg.pre()
                    request.addfinalizer(cfg.post)

    def get_driver_names(self, names):
        return [name for name in names if name in self.configs]


plugin = PsqlgraphPlugin()
