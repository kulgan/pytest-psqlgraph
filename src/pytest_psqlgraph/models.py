from typing import Any, Dict, List, Optional

import attr
import psqlgraph
from psqlgraph import ext
from sqlalchemy.ext.declarative import DeclarativeMeta
from typing_extensions import Protocol, TypedDict


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
    extra_bases: Optional[List[DeclarativeMeta]]
    default: Optional[bool]


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
            package_namespace=self.config.get("package_namespace"),
        )

    @property
    def package_namespace(self) -> Optional[str]:
        return self.config.get("package_namespace")

    @property
    def extra_bases(self) -> List[DeclarativeMeta]:
        return self.config.get("extra_bases", [])

    @property
    def is_default(self) -> Optional[bool]:
        return self.config.get("default", False)

    @property
    def orm_base(self) -> DeclarativeMeta:
        if not self.package_namespace:
            return psqlgraph.base.ORMBase
        return ext.get_orm_base(self.package_namespace)


class WithPsqlgraphData:
    ...
