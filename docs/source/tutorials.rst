Getting Started
===============

This describes how to quickly get started using pytest-psqlgraph

Step 1. Install
---------------
``pytest-flask`` is available on `PyPi`_, and can be easily installed via
``pip``::

    pip install pytest-psqlgraph


Step 2. Configure
-----------------

Define your psqlgraph config fixture in ``conftest.py``:

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
.. note:: Automatic Fixture Generation.

    While this fixture can be associated with any ``scope``, it is recommended to use ``session`` scope. The key of the configuration will be used to auto generate a fixture that returns a psqlgraph connection instance. The fixture will created and delete tables during initialization and tear down respectively. One a per test basis, the fixture will truncate tables as part of the tear down process for a particular test.

Step 3. Write and Run Test
--------------------------

Now you can depend on the fixture ``pg_driver`` in your tests

What’s next?
------------

The :ref:`features` section gives a more detailed view of available features, as
well as test fixtures and markers.

Consult the `pytest documentation <https://pytest.org/en/latest>`_ for more
information about pytest itself.


.. _PyPI: https://pypi.python.org/pypi/pytest-psqlgraph
