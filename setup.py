# Copyright 2022 Block, Inc.
"""Package configuration."""

import os

import setuptools


def long_description():
    """Generate long_description from project README."""
    cwd = os.path.abspath(os.path.dirname(__file__))
    readme_path = os.path.join(cwd, "README.md")
    assert os.path.exists(readme_path), "README.md not found"
    return open(readme_path, "r").read()


setuptools.setup(
    name="pyfu-usb",
    author="Block, Inc.",
    license="MIT",
    version="1.0.2",
    description="Python USB firmware update library.",
    long_description=long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/square/pyfu-usb",
    packages=setuptools.find_packages(),
    python_requires=">=3.7",
    package_data={
        "pyfu_usb": ["py.typed"],
    },
    install_requires=[
        "pyusb>=1.0.2",
        "rich>=12.2",
    ],
    extras_require={
        "dev": [
            "black~=22.3.0",
            "mypy==0.942",
            "types-setuptools~=57.4.14",
            "pylint~=2.7.0",
            "pre-commit~=2.18.1",
            "wheel~=0.37.1",
            "twine~=4.0.0",
            "pytest~=7.1.2",
            "coverage~=6.4",
        ]
    },
    entry_points={
        "console_scripts": ["pyfu-usb=pyfu_usb.__main__:main"],
    },
    keywords=["dfu-util", "pydfu"],
    classifiers=(
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ),
)
