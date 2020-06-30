import logging

import attr
import psqlgraph
import pytest
from _pytest.config import hookimpl
from _pytest.fixtures import FixtureLookupError

from pytest_psqlgraph import helpers

logger = logging.getLogger("pytest_psqlgraph.plugin")


def pytest_addoption(parser):
    group = parser.getgroup("psqlgraph")
    group.addoption("--drop-all", action="store_true", help="drop all tables before starting")


@attr.s
class PsqlGraphConfig(object):
    name = attr.ib(type=str)
    bases = attr.ib(type=list)
    config = attr.ib(type=dict)
    pg_driver = attr.ib(init=False, repr=False, hash=False, type=psqlgraph.PsqlGraphDriver)

    def __attrs_post_init__(self):
        self.pg_driver = psqlgraph.PsqlGraphDriver(**self.config)


class PsqlgraphPlugin(object):
    """ pytest Plugin class

    Attributes:
        config (dict[str, PsqlGraphConfig]): available configs
        markers (dict(str, helpers.FixtureHandler): markers
    """

    configs = {}
    fixture_handlers = {}

    @property
    def default_driver(self):
        if len(self.configs) == 1:
            return self.configs.keys()[0]
        return None

    def register_marker(self, name, fixture_handler):
        """ Registers a marker with

        Args:
            name:
            fixture_handler (helpers.FixtureHandler):
        """
        self.fixture_handlers[name] = fixture_handler

    @staticmethod
    def pytest_configure(config):
        config.addinivalue_line(
            "markers", "pgdata(name, driver, params): loads data for testing "
        )

    @hookimpl(tryfirst=True)
    def pytest_runtest_setup(self, item):
        item._pg_mark = None

        for marker in item.iter_markers(name="pgdata"):
            kwargs = marker.kwargs
            fixture_name = kwargs.get("name", "pgdata")
            handler = helpers.PgDataHandler(driver_name=kwargs.get("driver"), kwargs=kwargs.get("params"))
            self.register_marker(fixture_name, handler)

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
            self.register_marker(driver_name, helpers.FixtureHandler(driver_name))
            for base in cfg.bases:
                base.metadata.create_all(cfg.pg_driver.engine)
            self.configs[cfg.name] = cfg
        yield
        for _, cfg in self.configs.items():
            helpers.drop_tables(cfg.bases, cfg.pg_driver)

    @pytest.fixture(autouse=True)
    def __pg_fixture__(self, request):
        """ auto resolves named psqlgraph fixtures

        Args:
            request (_pytest.fixtures.SubRequest): pytest request
        """
        item = request._pyfuncitem
        for arg_name in request.fixturenames:
            try:
                request.getfixturevalue(arg_name)
            except FixtureLookupError:
                if arg_name in self.fixture_handlers:
                    handler = self.fixture_handlers[arg_name]  # type: helpers.FixtureHandler
                    pg_driver = self.get_driver(handler.driver_name)
                    item.funcargs[arg_name] = handler.pre(pg_driver)
                    item.addfinalizer(handler.post)
                    if handler.volatile:
                        self.fixture_handlers.pop(arg_name)

    def get_driver(self, driver=None):
        driver = driver or self.default_driver
        for name, cfg in self.configs.items():
            if name == driver:
                return cfg.pg_driver
        return None

    def get_driver_names(self, names):
        return [name for name in names if name in self.configs]


plugin = PsqlgraphPlugin()
