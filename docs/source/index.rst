.. pytest-psqlgraph documentation master file, created by
   sphinx-quickstart on Sun Jun 28 10:37:30 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

pytest-psqlgraph's documentation!
============================================
pytest-psqlgraph is a `pytest <https://pytest.org>`_ plugin that provides a set of useful tools for testing applications that utilize `psqlgraph <https://github.com/NCI-GDC/psqlgraph>`_.

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   tutorials
   features
   pytest_psqlgraph


Quick Start
-----------

Install via ``pip`` ::

   pip install pytest-psqlgraph

Define a ``psqlgraph_config`` fixture in ``conftest.py``

.. code-block:: python

   from typing import Dict

   import pytest
   from psqlgraph.base import ORMBase, VoidedBase

   from pytest_psqlgraph.models import DatabaseDriverConfig

   active_dictionary = None # load dictionary to use for this connection
   active_model = None # module containing all models to use for this connection

   @pytest.fixture(scope="session")
   def psqlgraph_config() -> Dict[str, DatabaseDriverConfig]:
      return dict(
         pg_driver=DatabaseDriverConfig(
            host="host",
            user="test",
            password="test",
            database="test",
            dictionary=active_dictionary,
            model=active_model,
            orm_base=ORMBase,
            extra_bases=[VoidedBase]
         )
      )

This will autogenerate a ``pg_driver`` fixture on demand.

.. code-block:: python

   def test_driver_initialized(pg_driver: psqlgraph.PsqlGraphDriver) -> None:
       """Tests fixture gets initialized correctly

       Tables are created and persistence happens
       Args:
           pg_driver (psqlgraph.PsqlGraphDriver): pg driver
       """
       assert pg_driver

       with pg_driver.session_scope() as s:
           pg_driver.nodes().count()

run test ::

   python -m pytest

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
