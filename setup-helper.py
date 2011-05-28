#!/usr/bin/python

from distutils.core import setup
import os.path
import glob
import sys

from setup import get_version_string

if __name__ == "__main__":
    setup(
        name="btrfs-gui-helper",
        version=get_version_string(),
        description="A graphical user interface for btrfs functions",
        author="Hugo Mills",
        author_email="hugo@carfax.org.uk",
        url="http://carfax.org.uk/btrfs-gui",
        packages=["btrfsgui", "btrfsgui.hlp"],
        scripts=["btrfs-gui-helper"],
        )
