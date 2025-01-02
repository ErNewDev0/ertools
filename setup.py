import os
import re
from setuptools import find_packages, setup


def read_requirements():
    """Reads the requirements.txt file and returns a list of dependencies."""
    try:
        with open("requirements.txt", encoding="utf-8") as f:
            return f.read().splitlines()
    except FileNotFoundError:
        print("Warning: requirements.txt not found. No dependencies will be installed.")
        return []


def read(fname):
    """Reads a file and returns its content."""
    try:
        with open(os.path.join(os.path.dirname(__file__), fname), encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


with open("ertools/__init__.py", encoding="utf-8") as f:
    version = re.findall(r"__version__ = \"(.+)\"", f.read())[0]

setup(
    name="ertools",
    version=version,
    description="Library for Chatbot",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="ErNewDev0",
    author_email="admin@ryppain.com",
    url="https://pypi.org/JustR",
    license="MIT",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8, <3.13",
    install_requires=read_requirements(),
)