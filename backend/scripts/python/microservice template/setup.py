# -*- coding: utf-8 -*-

from setuptools import setup, find_packages  # type: ignore
from os import path
import myservice


with open(path.join(".", "README.md"), encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", encoding="utf-8") as f:
    install_requires = [
        line.strip()
        for line in f.read().split("\n")
        if not line.strip().startswith("#") and not line.strip().startswith("git+")
    ]

extras_require = {}

with open("requirements_test.txt", encoding="utf-8") as f:
    extras_require["test"] = [line.strip() for line in f.read().split("\n") if not line.strip().startswith("#")]


setup(
    name="myservice",
    version=myservice.__version__,
    description="my project description",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=install_requires,
    extras_require=extras_require,
    include_package_data=True,
    package_data={"myservice": ["resources/*"]}, # images, etc
)
