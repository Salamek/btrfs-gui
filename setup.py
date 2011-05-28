#!/usr/bin/python3

from distutils.core import setup
from subprocess import Popen, PIPE
import os.path
import glob
import sys

def get_version_string():
	"""Muck around with git to work out what the version string should
	be: pick the last tag in the list, see if it matches the current
	git revision, and append a revision ID if they're not the same.
	"""
	try:
		data, err = Popen(["git", "tag", "-l"],
						  stdout=PIPE).communicate()
		tags = list(filter(lambda x: x.startswith("v"),
						   data.decode().split("\n")))
		version = tags[-1]
		data, err = Popen(["git", "log", "-1", "--pretty=format:%H", version],
						  stdout=PIPE).communicate()
		last_git_id = data.decode().split("\n")[0]
		data, err = Popen(["git", "log", "-1", "--pretty=format:%H"],
						  stdout=PIPE).communicate()
		this_git_id = data.decode().split("\n")[0]
		if last_git_id != this_git_id:
			version += "-" + this_git_id[:8]
	except Exception as ex:
		print(ex)
		version = "unknown"
	return version

if __name__ == "__main__":
	if sys.version_info.major < 3:
		print("""btrfs-gui requires python 3.
If you want to install the btrfs-gui root helper on its own, use the
setup-helper.py script instead.""")
		sys.exit(1)

	setup(
		name="btrfs-gui",
		version=get_version_string(),
		description="A graphical user interface for btrfs functions",
		author="Hugo Mills",
		author_email="hugo@carfax.org.uk",
		url="http://carfax.org.uk/btrfs-gui",
		packages=["btrfsgui", "btrfsgui.hlp", "btrfsgui.gui"],
		scripts=["btrfs-gui", "btrfs-gui-helper"],
		data_files=[("share/btrfs-gui/img",
					 glob.glob(os.path.join("img", "*.gif")) + ["img/icons.svg"]),
					],
		)
