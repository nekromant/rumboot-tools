#!/usr/bin/env python3
#
# Copyright (c) 2018 Andrew Andrianov <andrew@ncrmnt.org>
#

import rumboot
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name = "rumboot-tools",
    version = rumboot.__version__,
    packages=find_packages(),
    install_requires = [
        "pyusb", #HACK: Needed for pygpiotools installation for some weird pip reason
        "pyserial", 
        "pyft232", 
        "parse", 
        "xmodem", 
        "tqdm", 
        "pyyaml", 
        "hexdump",
        "netifaces", 
        "netaddr",
        "getmac",
        "heatshrink2",
        "pyqt5",
        "pygpiotools",
        "argcomplete",
        "humanfriendly"
        ],

    extras_require = {
    },
    entry_points = {
        "console_scripts": [
            "rumboot-packimage = rumboot_packimage.frontend:cli",
            "rumboot-xrun = rumboot_xrun.frontend:cli",
            "rumboot-xflash = rumboot.flashing:rumboot_start_flashing",
            "rumboot-daemon = rumboot_daemon.frontend:cli",
            "rumboot-combine = rumboot_combine.frontend:cli",
            "rumboot-flashrom = rumboot_flashrom.frontend:cli",
            "rumboot-gdb = rumboot_gdb.frontend:cli",
        ],
    },
    include_package_data=True,
    description = "RumBoot ROM Loader Tools",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    keywords = "rumboot image",
    url = "http://github.com/RC-MODULE/rumboot-tools",
    author = "Andrew Andrianov",
    author_email = "andrew@ncrmnt.org",
    license = "GPL",
    platforms = "any",
    classifiers = [
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Linux",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: Software Development",
    ],
)
