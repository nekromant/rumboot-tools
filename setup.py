#!/usr/bin/env python3
#
# Copyright (c) 2018 Andrew Andrianov <andrew@ncrmnt.org>
#

import rumboot_packimage
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name = "rumboot-tools",
    version = rumboot_packimage.__version__,
    packages = find_packages(exclude=["doc", "tests"]),
    install_requires = ["pyserial", "pyft232", "parse", "xmodem"],
    extras_require = {
        "usb": ["pyusb>=1.0.0"]
    },
    entry_points = {
        "console_scripts": [
            "rumboot-packimage = rumboot_packimage.frontend:cli",
            "rumboot-xrun = rumboot_xrun.frontend:cli",
        ],
    },
    description = "RumBoot loader tools",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    keywords = "rumboot image",
    url = "http://git.module.ru/verification-components/rumboot-packimage.py.git",
    author = "Andrew Andrianov",
    author_email = "andrew@ncrmnt.org",
    license = "MIT",
    platforms = "any",
    classifiers = [
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: Software Development",
    ],
)
