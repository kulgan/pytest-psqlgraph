import logging

import attr
import psqlgraph
import pytest
from _pytest.fixtures import FixtureLookupError

from pytest_psqlgraph import helpers


logger = logging.getLogger("pytest_psqlgraph.plugin")


def pytest_addoption(parser):
    group = parser.getgroup("psqlgraph")
    group.addoption("--drop-all", action="store_true", help="drop all tables before starting")


def pytest_configure(config):
    pass


def pytest_sessionstart(session):
    print(session)


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

    @pytest.fixture(scope="session", autouse=True)
    def psqlgraph(self, request, pg_config):
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


plugin = PsqlgraphPlugin()
