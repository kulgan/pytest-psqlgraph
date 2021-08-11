from os import path

import pkg_resources
import yaml
from psqlgraph import Edge, Node, pg_property

data_dir = pkg_resources.resource_filename("tests", "data/dictionary.yaml")

with open(data_dir) as f:
    dictionary = yaml.safe_load(f.read())


class Dictionary:
    schema = dictionary


class PersonMixin:

    _pg_edges = {}

    @pg_property
    def name(self, val):
        self._set_property("name", val)


class Father(Node, PersonMixin):

    __label__ = "father"


class Son(Node, PersonMixin):

    __label__ = "son"


class Mother(Node, PersonMixin):

    __label__ = "mother"


class Daughter(Node, PersonMixin):

    __label__ = "daughter"


class HusbandWifeEdge(Edge):

    __src_class__ = "Father"
    __dst_class__ = "Mother"
    __src_dst_assoc__ = "wife"
    __dst_src_assoc__ = "husband"


class FatherSonEdge(Edge):

    __src_class__ = "Father"
    __dst_class__ = "Son"
    __src_dst_assoc__ = "sons"
    __dst_src_assoc__ = "father"


class FatherDaughterEdge(Edge):
    __src_class__ = "Father"
    __dst_class__ = "Daughter"
    __src_dst_assoc__ = "daughters"
    __dst_src_assoc__ = "father"


class MotherSonEdge(Edge):

    __src_class__ = "Mother"
    __dst_class__ = "Son"
    __src_dst_assoc__ = "sons"
    __dst_src_assoc__ = "mother"


class MotherDaughterEdge(Edge):
    __src_class__ = "Mother"
    __dst_class__ = "Daughter"
    __src_dst_assoc__ = "daughters"
    __dst_src_assoc__ = "mother"


Father._pg_edges.update(
    {
        "sons": {"type": Son, "backref": "father"},
        "daugthers": {"type": Daughter, "backref": "father"},
        "wife": {"type": Mother, "backref": "husband"},
    }
)


Mother._pg_edges.update(
    {
        "sons": {"type": Son, "backref": "mother"},
        "daughters": {"type": Daughter, "backref": "mother"},
        "husband": {"type": Father, "backref": "wife"},
    }
)

Son._pg_edges.update(
    {
        "father": {
            "type": Father,
            "backref": "sons",
            "required": True,
        },
        "mother": {
            "type": Mother,
            "backref": "sons",
            "required": True,
        },
    }
)

Daughter._pg_edges.update(
    {
        "father": {
            "type": Father,
            "backref": "daughters",
            "required": True,
        },
        "mother": {
            "type": Mother,
            "backref": "daughters",
            "required": True,
        },
    }
)
