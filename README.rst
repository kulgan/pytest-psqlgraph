pytest-psqlgraph
================

|PyPI version| |conda-forge version| |Python versions| |ci| |Documentation status|

An extension for `pytest <https://pytest.org>`_ provide useful tools for testing applications that use `psqlgraph <https://github.com/NCI-GDC/psqlgraph>`_

Quick Start
-----------
Install dependency ::

    $ pip install pytest-psqlgraph

Setup ``pg_config`` fixture in main ``conftest.py``:

.. code-block:: python
    import pytest

    @pytest.fixture
    def pg_config():
        return {
            "pg_driver": {
                "host": "localhost",
                "user": "username",
                "password": "pword",
                "database": "db_name"
            }
        }

..

This exposes a request scoped fixture that can be auto used:

.. code-block:: python
    def test_something(pg_driver):
        with pg_driver.session_scoped() as s:
            s.add(Node(..))
..

See docs for more

.. |PyPI version| image:: https://img.shields.io/pypi/v/pytest-psqlgraph.svg
   :target: https://pypi.python.org/pypi/pytest-psqlgraph
   :alt: PyPi version

.. |conda-forge version| image:: https://img.shields.io/conda/vn/conda-forge/pytest-psqlgraph.svg
   :target: https://anaconda.org/conda-forge/pytest-psqlgraph
   :alt: conda-forge version

.. |ci| image:: https://github.com/kulgan/pytest-psqlgraph/workflows/ci/badge.svg
   :target: https://github.com/kulgan/pytest-psqlgraph/actions
   :alt: CI status

.. |Python versions| image:: https://img.shields.io/pypi/pyversions/pytest-psqlgraph.svg
   :target: https://pypi.org/project/pytest-psqlgraph
   :alt: PyPi downloads

.. |Documentation status| image:: https://readthedocs.org/projects/pytest-psqlgraph/badge/?version=latest
   :target: https://pytest-psqlgraph.readthedocs.org/en/latest/
   :alt: Documentation status
