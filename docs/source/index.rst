.. pytest-psqlgraph documentation master file, created by
   sphinx-quickstart on Sun Jun 28 10:37:30 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pytest-psqlgraph's documentation!
============================================
Pytest-Psqlgraph is a `pytest <https://pytest.org>`_ plugin that provides a set of useful tools for testing applications that utilize `psqlgraph <https://github.com/NCI-GDC/psqlgraph>`_.

User's Guide
------------

.. toctree::
   :maxdepth: 4
   :caption: Contents:

   tutorials
   features
   contributing


Quick Start
-----------
Install via ``pip``::
   pip install pytest-psqlgraph

Define a ``pg_config`` fixture in ``conftest.py``:
.. code-block:: python
   import pytest

   @pytest.fixture(scope="session")
   def pg_config():
      return dict(
         pg_driver=dict(
            host="host",
            user="test",
            password="test",
            database="test",
         )
      )

run test ::
   python -m pytest




Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
