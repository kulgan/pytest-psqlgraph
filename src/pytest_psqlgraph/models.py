from typing import Any, Dict, Iterable, List, Optional, Union

import attr
import psqlgraph
from psqlgraph import ext
from sqlalchemy.ext.declarative import DeclarativeMeta
from typing_extensions import Literal, Protocol, TypedDict

UniqueFieldType = Literal["node_id", "submitter_id"]


class Edge(TypedDict, total=False):
    dst: str
    label: str
    src: str
    tag: str


class Node(TypedDict, total=False):
    node_id: str
    submitter_id: str
    label: str


class SchemaData(TypedDict, total=False):
    description: str
    edges: List[Edge]
    extends: str
    nodes: List[Node]
    summary: Dict[str, int]
    unique_field: str


class PostProcessor(Protocol):
    def __call__(self, node: psqlgraph.Node) -> None:
        ...


class PsqlgraphDataMark(TypedDict, total=False):
    name: str
    driver_name: str
    data_dir: str
    resource: Union[str, SchemaData]
    unique_key: str
    mock_all_props: bool
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
            package_namespace=self.config.get("package_namespace"),
        )

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
        return ext.get_orm_base(self.package_namespace)

    @property
    def model(self) -> Optional[DataModel]:
        return self.config.get("model")

    @property
    def globals(self) -> Optional[Dict[str, Any]]:
        return self.config.get("globals")

    @property
    def dictionary(self) -> Optional[Dictionary]:
        return self.config.get("dictionary")
