"""
A simple setup.py.
Installs the `shared` depdendencies to environment.
Intended to be installed into service environments to access `shared` modules.
"""

from setuptools import setup, find_namespace_packages

setup(
    name="meridian-shared",
    version="0.1",
    packages=find_namespace_packages(include=["shared.*"]),
    install_requires=[
        "bottle",
        "msgpack",
        "toml",
        "requests"
    ]
)
