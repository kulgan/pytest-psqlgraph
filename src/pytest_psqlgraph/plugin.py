import logging
from typing import Dict

from _pytest import fixtures as f
from _pytest import main as m
from _pytest import python as p

from . import helpers, models

logger = logging.getLogger(__name__)
CONFIG_FIXTURE_NAME: str = "psqlgraph_config"
ACTIVE_DB_FIXTURES: Dict[str, helpers.DatabaseFixture] = {}


def pytest_addoption(parser):
    group = parser.getgroup("psqlgraph")
    group.addoption(
        "--drop-all", action="store_true", help="drop all tables before starting"
    )


def pytest_configure(config: f.Config) -> None:
    config.addinivalue_line(
        "markers", "use_psqlgraph_data(name, driver, params): loads data for testing "
    )


def pytest_collection_finish(session: m.Session) -> None:
    """A psqlgraph driver instance

    Initializes the database tables and makes fixtures available
    Example:
        code-block::
            {"g": {
                "host": "localhost",
                "user": "test",
                "password": "test",
                "database": "test_db",
                "extra_bases": [],
                "models": model_module,
                "dictionary": dictionary instance
                }
            }

    """
    if not session.items:
        return

    item = session.items[0]
    request: f.SubRequest = item._request

    cfg: Dict[str, models.DatabaseDriverConfig] = request.getfixturevalue(
        CONFIG_FIXTURE_NAME
    )

    for name, config in cfg.items():

        if name in ACTIVE_DB_FIXTURES:
            continue

        driver = models.DatabaseDriver(config)
        logger.info("initializing fixture {0}".format(name))

        fixture = helpers.DatabaseFixture(name, driver)
        fixture.pre_config()
        session.addfinalizer(fixture.post_config)
        ACTIVE_DB_FIXTURES[name] = fixture


def pytest_runtest_setup(item: p.Function) -> None:
    inject_psqlgraph_fixture(item)

    # for marker in item.iter_markers(name="pgdata"):
    #     kwargs = marker.kwargs
    #     fixture_name = kwargs.get("name", "pgdata")
    # handler = helpers.PgDataHandler(
    #     driver_name=kwargs.get("driver"), kwargs=kwargs.get("params")
    # )
    # self.register_fixture(fixture_name, handler)


def inject_psqlgraph_fixture(item: p.Function) -> None:
    """Resolves and setups psqldriver fixtures based on psqlgraph_config entries"""

    for pg_fixture in ACTIVE_DB_FIXTURES:
        if pg_fixture not in item.fixturenames:
            continue
        fixture = ACTIVE_DB_FIXTURES[pg_fixture]
        item.funcargs[pg_fixture] = fixture.pre_test()
        item.addfinalizer(fixture.post_test)
