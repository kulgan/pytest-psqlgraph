from typing import Any, Dict, Iterable, List, Optional, Union

import attr
import psqlgml
import psqlgraph
from sqlalchemy.ext.declarative import DeclarativeMeta

from pytest_psqlgraph.typings import Protocol, TypedDict


class PostProcessor(Protocol):
    def __call__(self, node: psqlgraph.Node) -> None:
        ...


class PsqlgraphDataMark(TypedDict, total=False):
    name: str
    driver_name: str
    data_dir: str
    resource: Union[str, psqlgml.GmlData]
    post_processors: Iterable[PostProcessor]


class Dictionary(Protocol):
    schema: Dict[str, Any]


class DataModel(Protocol):
    ...


class DatabaseDriverConfig(TypedDict):
    host: str
    user: str
    password: str
    database: str
    package_namespace: Optional[str]
    model: DataModel
    dictionary: Dictionary
    orm_base: Optional[DeclarativeMeta]
    extra_bases: Optional[List[DeclarativeMeta]]
    globals: Optional[Dict[str, Any]]


@attr.s(auto_attribs=True)
class DatabaseDriver:
    config: DatabaseDriverConfig
    g: psqlgraph.PsqlGraphDriver = attr.ib(init=False)

    def __attrs_post_init__(self) -> None:
        self.g = psqlgraph.PsqlGraphDriver(
            host=self.config["host"],
            user=self.config["user"],
            database=self.config["database"],
            password=self.config["password"],
        )
        self.g.package_namespace = self.config.get("package_namespace")

    @property
    def package_namespace(self) -> Optional[str]:
        return self.config.get("package_namespace")

    @property
    def extra_bases(self) -> List[DeclarativeMeta]:
        return self.config.get("extra_bases") or []

    @property
    def orm_base(self) -> DeclarativeMeta:
        if not self.package_namespace:
            return psqlgraph.base.ORMBase
        return self.config.get("orm_base") or psqlgraph.base.ORMBase

    @property
    def model(self) -> Optional[DataModel]:
        return self.config.get("model")

    @property
    def globals(self) -> Optional[Dict[str, Any]]:
        return self.config.get("globals")

    @property
    def dictionary(self) -> Dictionary:
        return self.config["dictionary"]

    def create_all(self) -> None:
        self.orm_base.metadata.create_all(self.g.engine)

    def drop_all(self) -> None:
        self.orm_base.metadata.drop_all(self.g.engine)
