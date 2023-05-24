#!/usr/bin/env python

from setuptools import setup  # type: ignore

if __name__ == "__main__":
    setup(
        author="Fabian Keller",
        package_data={
            "typed_argparse": ["py.typed"],
        },
        include_package_data=True,
        install_requires=[
            "typing-extensions",
        ],
    )
