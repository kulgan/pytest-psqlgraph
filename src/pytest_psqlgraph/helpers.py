""" Helper functions """

import psqlgraph
from psqlgraph import ext
from psqlgraph.base import ORMBase


def truncate_tables(pg_driver):
    """ Truncates all entries in the datanase

    Args:
        pg_driver (psqlgraph.PsqlGraphDriver): active driver
    """
    with pg_driver.engine.begin() as conn:
        for table in reversed(pg_driver.engine.table_names()):
            conn.execute('delete from {} cascade'.format(table))


def create_tables(pg_driver, namespace):
    base = ORMBase if namespace is None else ext.get_orm_base(namespace)
    psqlgraph.create_all(pg_driver.engine, base=base)


def drop_tables(bases, pg_driver):
    """ Drops all tables in the listed orm_bases

    Args:
        bases (list[sqlalchemy.Base):
        pg_driver (psqlgraph.PsqlGraphDriver):
    """
    for base in bases:
        base.metadata.drop_all(pg_driver.engine)


def load_data(source):
    """ Load data from json/yaml file

        Args:
            source (str): source filename

    """
