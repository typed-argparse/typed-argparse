#!/usr/bin/env python

import setuptools  # type: ignore

if __name__ == "__main__":
    setuptools.setup(
        package_data={
            "typed_argparse": ["py.typed"],
        },
        include_package_data=True,
        install_requires=[
            "typing-extensions",
        ],
    )
