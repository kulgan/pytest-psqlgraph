import logging
from typing import Dict, cast

import pytest
from _pytest import fixtures as f
from _pytest import main as m
from _pytest import python as p

from . import helpers, models

logger = logging.getLogger(__name__)
CONFIG_FIXTURE_NAME: str = "psqlgraph_config"
MARKER_NAME: str = "psqlgraph_data"
ACTIVE_DB_FIXTURES: Dict[str, helpers.DatabaseFixture] = {}


def pytest_addoption(parser: m.Parser) -> None:
    group = parser.getgroup("psqlgraph")
    group.addoption("--drop-all", action="store_true", help="drop all tables before starting")


def pytest_configure(config: f.Config) -> None:
    config.addinivalue_line(
        "markers",
        "{}(host, user, password, database, model, dictionary): loads data for testing ".format(
            MARKER_NAME
        ),
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

    item = cast(p.Function, session.items[0])
    request: f.FixtureRequest = item._request

    try:
        cfg: Dict[str, models.DatabaseDriverConfig] = request.getfixturevalue(CONFIG_FIXTURE_NAME)
        for name, config in cfg.items():

            if name in ACTIVE_DB_FIXTURES:
                continue

            driver = models.DatabaseDriver(config)
            logger.debug(f"initializing fixture {name}")

            fixture = helpers.DatabaseFixture(name, driver)
            fixture.pre_config()
            session.addfinalizer(fixture.post_config)
            ACTIVE_DB_FIXTURES[name] = fixture

    except pytest.FixtureLookupError:
        print("fixture not found")
        logger.warning(
            "pytest-psqlgraph config fixture not found, pytest-psqlgraph will not work correctly",
            exc_info=True,
        )


def pytest_runtest_setup(item: p.Function) -> None:
    inject_psqlgraph_fixture(item)

    for marker in item.iter_markers(name=MARKER_NAME):
        inject_marker_data(marker, item)


def inject_psqlgraph_fixture(item: p.Function) -> None:
    """Resolves and setups psqlgraph driver fixtures based on psqlgraph_config entries"""

    for pg_fixture in ACTIVE_DB_FIXTURES:
        if pg_fixture not in item.fixturenames:
            continue
        fixture = ACTIVE_DB_FIXTURES[pg_fixture]
        item.funcargs[pg_fixture] = fixture.pre_test()
        item.addfinalizer(fixture.post_test)


def inject_marker_data(marker: models.PytestMark, item: p.Function) -> None:
    mark: models.PsqlgraphDataMark = cast(models.PsqlgraphDataMark, marker.kwargs)
    driver_name = mark["driver_name"]

    if driver_name not in ACTIVE_DB_FIXTURES:
        raise ValueError(
            "provided psqlgraph driver {} is not defined in the fixture psqlgraph_config".format(
                driver_name
            )
        )
    fixture = ACTIVE_DB_FIXTURES[driver_name]
    handler = helpers.MarkHandler(mark, fixture)
    try:
        item.funcargs[mark["name"]] = handler.pre()
        item.addfinalizer(handler.post)
    except Exception as e:
        logger.error(f"pytest-psqlgraph ran into an error while loading data: {e}", exc_info=True)
        raise e
