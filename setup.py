from os import path

from setuptools import find_packages
from setuptools import setup


here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md")) as f:
    long_description = f.read()


setup(
    name="pytest-psqlgraph",
    license="Apache 2.0",
    author="Rowland Ogwara",
    author_email="r.ogwara@gmail.com",
    maintainer="Rowland Ogwara",
    maintainer_email="r.ogwara@gmail.com",
    use_scm_version={
        "local_scheme": "dirty-tag",
        "version_scheme": "release-branch-semver"
    },
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kulgan/pytest-psqlgraph",
    project_urls={
        "source": "https://github.com/kulgan/pytest-psqlgraph"
    },
    classifiers=[
        "Development Status :: 2 - Alpha",
        "Environment :: Plugins",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        'Operating System :: OS Independent',
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
    ],
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    keywords="psqlgraph, pytest, testing, postgresql",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    zip_safe=True,
    install_requires=[
        "attrs",
        "pytest>=4.5",
        "PyYaml>=5",
        "psqlgraph @ git+ssh://git@github.com/NCI-GDC/psqlgraph.git@3.0.0a2#egg=psqlgraph"
    ],
    extras_require={
        "dev": [
            "coverage[toml]",
            "flake8",
            "pre-commit",
            "pytest",
            "pytest-cov",
            "sphinx",
            "tox",
        ]
    },
    setup_requires=[
        "setuptools_scm"
    ],
    entry_points={
        "pytest11": [
            "psqlgraph = pytest_psqlgraph.plugin:plugin"
        ]
    }
)
