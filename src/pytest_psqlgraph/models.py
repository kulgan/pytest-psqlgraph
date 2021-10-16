from typing import Any, Dict, Iterable, Optional, Union

import attr
import psqlgml
import psqlgraph
from sqlalchemy.ext.declarative import DeclarativeMeta

from pytest_psqlgraph.typings import Protocol, TypedDict


class PostProcessor(Protocol):
    """A callable that allows users take action just after the nodes are generated"""

    def __call__(self, node: psqlgraph.Node) -> None:
        ...


class PsqlgraphDataMark(TypedDict, total=False):
    name: str
    driver_name: str
    data_dir: str
    resource: Union[str, psqlgml.GmlData]
    post_processors: Iterable[PostProcessor]


class Dictionary(Protocol):
    """A dictionary template

    Attributes:
        schema: node name and schema pairs
    """

    schema: Dict[str, psqlgml.DictionarySchemaDict]


class DataModel(Protocol):
    ...


@attr.s(frozen=True, auto_attribs=True)
class DatabaseDriverConfig:
    """psqlgraph database configuration data

    Attributes:
        host: postgres database hostname with port (if non default)
        user: postgres database username
        password: postgres database user password
        database: postgres database name to connect to
        package_namespace: optional parameter used to demarcate driver model classes
        model: The python module containing all the models associated with this database
        dictionary: The instance containing the dictionary definitions
        orm_base: Optional sqlalchemy declarative base used by all models, this defaults to
            psqlgraph ORMBase
        extra_bases: Iterable of bases that needs to be created/destroyed as part of the driver
        globals: optional default property keys and values used for all nodes created
    """

    host: str
    user: str
    password: str
    database: str
    model: DataModel
    dictionary: Dictionary
    package_namespace: Optional[str] = None
    orm_base: Optional[DeclarativeMeta] = None
    extra_bases: Optional[Iterable[DeclarativeMeta]] = None
    globals: Optional[Dict[str, Any]] = None


@attr.s(auto_attribs=True)
class DatabaseDriver:
    config: DatabaseDriverConfig
    g: psqlgraph.PsqlGraphDriver = attr.ib(init=False)

    def __attrs_post_init__(self) -> None:
        self.g = psqlgraph.PsqlGraphDriver(
            host=self.config.host,
            user=self.config.user,
            database=self.config.database,
            password=self.config.password,
        )
        self.g.package_namespace = self.config.package_namespace

    @property
    def package_namespace(self) -> Optional[str]:
        return self.config.package_namespace

    @property
    def extra_bases(self) -> Iterable[DeclarativeMeta]:
        return self.config.extra_bases or []

    @property
    def orm_base(self) -> DeclarativeMeta:
        if not self.package_namespace:
            return psqlgraph.base.ORMBase
        return self.config.orm_base or psqlgraph.base.ORMBase

    @property
    def model(self) -> Optional[DataModel]:
        return self.config.model

    @property
    def globals(self) -> Optional[Dict[str, Any]]:
        return self.config.globals

    @property
    def dictionary(self) -> Dictionary:
        return self.config.dictionary

    def create_all(self) -> None:
        self.orm_base.metadata.create_all(self.g.engine)

    def drop_all(self) -> None:
        self.orm_base.metadata.drop_all(self.g.engine)
