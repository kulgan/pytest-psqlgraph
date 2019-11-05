import io

from setuptools import find_packages
from setuptools import setup

version = "0.0.1-alpha"

def read_file(file_name):
    pass

setup(
    name="pytest-psqlgraph",
    packages=find_packages(exclude=["tests"]),
    platform="any"
)