from _pytest.config import Config


def pytest_psqlgraph_hook(config: Config):
    """Adds pg_drivers"""
