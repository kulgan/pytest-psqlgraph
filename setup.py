from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.rst")) as f:
    long_description = f.read()


setup(
    name="pytest-psqlgraph",
    license="Apache 2.0",
    author="Rowland Ogwara",
    author_email="r.ogwara@gmail.com",
    maintainer="Rowland Ogwara",
    maintainer_email="r.ogwara@gmail.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kulgan/pytest-psqlgraph",
    project_urls={"source": "https://github.com/kulgan/pytest-psqlgraph"},
    classifiers=[
        "Development Status :: 2 - Alpha",
        "Environment :: Plugins",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
    ],
    python_requires=">=3.6",
    keywords="psqlgraph, pytest, testing, postgresql",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    zip_safe=True,
    install_requires=[
        "attrs",
        "pytest>=4.5",
        "PyYaml>=5",
        "psqlgraph @ git+https://github.com/NCI-GDC/psqlgraph.git@3.3.0#egg=psqlgraph",
        "sqlalchemy<1.4",
        "typing_extensions; python_version < '3.8'",
    ],
    extras_require={
        "dev": [
            "coverage[toml]",
            "flake8",
            "pre-commit",
            "pytest",
            "pytest-cov",
            "sphinx",
            "mypy==0.910",
            "sphinxcontrib-napoleon",
        ]
    },
    setup_requires=["setuptools_scm"],
    entry_points={"pytest11": ["psqlgraph = pytest_psqlgraph.plugin"]},
)
