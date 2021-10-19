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
    group.addoption("--data-dir", help="default test data files directory")


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
        print(f"fixture '{CONFIG_FIXTURE_NAME}'not found")
        logger.warning(
            f"pytest-psqlgraph config fixture '{CONFIG_FIXTURE_NAME}' not found",
            exc_info=True,
        )


def __get_or_make_driver_fixture__(arg_name: str, request: f.SubRequest) -> None:
    """Check if a driver fixture is currently defined and create, inject it if it is not defined.

    Args:
        arg_name: name for the fixture
        request: pytest request context
    """
    try:
        request.getfixturevalue(arg_name)
    except f.FixtureLookupError:
        if arg_name not in ACTIVE_DB_FIXTURES:
            return
        print(arg_name)
        fixture = ACTIVE_DB_FIXTURES[arg_name]
        inject_driver_fixture(fixture, request)


def inject_marker_data(mark: models.PsqlgraphDataMark, item: p.Function) -> None:
    """Resolves data for the custom psqlgraph data

    Examples:
        .. code-block::

          @pytest.mark.psqlgraph_data(
            name="pg_data",
            driver_name="pg_driver",
            data_dir=here,
            resource="sample.yaml",
            post_processors=[append_mr],
          )
          def test_example(pg_driver: psqlgraph.PsqlGraphDriver, pg_data: List[psqlgraph.Node]) -> None:
            ...

    """
    driver_name = mark["driver_name"]

    __get_or_make_driver_fixture__(driver_name, item._request)
    if driver_name not in ACTIVE_DB_FIXTURES:
        raise ValueError(
            f"No driver '{driver_name}' defined in the fixture psqlgraph_config, "
            f"expected one of {list(ACTIVE_DB_FIXTURES.keys())}"
        )
    fixture = ACTIVE_DB_FIXTURES[driver_name]
    handler = helpers.MarkHandler(mark, fixture)
    try:
        name = mark.get("name", "__psqlgraph_data__")
        item.funcargs[name] = handler.pre()
        item.addfinalizer(handler.post)
    except Exception as e:
        logger.error(f"pytest-psqlgraph ran into an error while loading data: {e}", exc_info=True)
        raise e


def pytest_runtest_setup(item: p.Function) -> None:

    for marker in item.iter_markers(name=MARKER_NAME):
        mark = cast(models.PsqlgraphDataMark, marker.kwargs)
        mark["data_dir"] = mark.get("data_dir") or item.config.getoption("--data-dir")
        inject_marker_data(mark, item)


def inject_driver_fixture(fixture: helpers.DatabaseFixture, request: f.SubRequest) -> None:
    """Resolves and setups psqlgraph driver fixtures based on psqlgraph_config entries"""

    value = fixture.pre_test()
    fd = f.FixtureDef(
        argname=fixture.name,
        baseid=None,
        fixturemanager=request._fixturemanager,
        func=lambda: value,
        scope="function",
        params=None,
    )
    fd.addfinalizer(fixture.post_test)
    fd.cached_result = (value, 0, None)

    old_fd = request._fixture_defs.get(fixture.name)  # noqa
    add_fixturename = fixture.name not in request.fixturenames

    def fin() -> None:
        request._fixturemanager._arg2fixturedefs[fixture.name].remove(fd)  # noqa
        request._fixture_defs[fixture.name] = old_fd  # noqa

        if add_fixturename:
            request._pyfuncitem._fixtureinfo.names_closure.remove(fixture.name)  # noqa

    request.addfinalizer(fin)

    # inject fixture definition
    request._fixturemanager._arg2fixturedefs.setdefault(fixture.name, []).insert(0, fd)  # noqa
    # inject fixture value in request cache
    request._fixture_defs[fixture.name] = fd  # noqa
    if add_fixturename:
        request._pyfuncitem._fixtureinfo.names_closure.append(fixture.name)  # noqa


@pytest.fixture(autouse=True)
def __pg_driver_fixture__(request: f.SubRequest) -> None:
    """auto resolves named psqlgraph fixtures"""

    for arg_name in ACTIVE_DB_FIXTURES:
        __get_or_make_driver_fixture__(arg_name, request)
