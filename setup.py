#!/usr/bin/python3

from distutils.core import setup
from subprocess import call, Popen, PIPE
import os
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

def convert2to3():
	"""Automatically convert the python2 bits to python3 before installing
	"""
	patch = open("convert.patch", "w")
	devnull = open("/dev/null", "w")
	call(["2to3", "btrfsgui/hlp", "btrfs-gui-helper"],
		 stdout=patch, stderr=devnull)
	patch.close()
	patch = open("convert.patch", "r")
	call(["patch", "-p0", "-b", "-z.orig-py2"], stdin=patch)
	patch.close()

def reset2to3():
	"""Undo what convert2to3() did
	"""
	for dirpath, dirnames, filenames in os.walk("btrfsgui"):
		for f in filenames:
			orig, ext = os.path.splitext(f)
			if ext == ".orig-py2":
				os.rename(os.path.join(dirpath, f),
						  os.path.join(dirpath, orig))

def convert_wrapper(fn):
	"""Wrap up a function with a reasonably safe convert/restore
	operation, using convert2to3 and reset2to3.
	"""
	def rf():
		if sys.version_info[0] >= 3:
			# Convert the python2 bits in the source to python3
			convert2to3()
		try:
			fn()
		finally:
			if sys.version_info[0] >= 3:
				# Restore the original files
				reset2to3()
	return rf

@convert_wrapper
def setup_gui():
	"""Set up the full package, including the helper.
	"""
	setup(
		name="btrfs-gui",
		version=get_version_string(),
		description="A graphical user interface for btrfs functions",
		author="Hugo Mills",
		author_email="hugo@carfax.org.uk",
		url="http://carfax.org.uk/btrfs-gui",
		packages=["btrfsgui", "btrfsgui.gui", "btrfsgui.hlp"],
		scripts=["btrfs-gui", "btrfs-gui-helper"],
		data_files=[("share/btrfs-gui/img",
					 glob.glob(os.path.join("img", "*.gif")) + ["img/icons.svg"]),
					],
		)

@convert_wrapper
def setup_helper():
	"""Set up just the helper
	"""
	pyv = ""
	if sys.version_info[0] < 3:
		pyv = "-py2"
	setup(
		name="btrfs-gui-helper" + pyv,
		version=get_version_string(),
		description="A graphical user interface for btrfs functions: user-space parts",
		author="Hugo Mills",
		author_email="hugo@carfax.org.uk",
		url="http://carfax.org.uk/btrfs-gui",
		packages=["btrfsgui", "btrfsgui.hlp"],
		scripts=["btrfs-gui-helper"],
		)

if __name__ == "__main__":
	if sys.version_info[0] < 3:
		print("""btrfs-gui requires python 3.
If you want to install the btrfs-gui root helper on its own, use the
setup-helper.py script instead.""")
		sys.exit(1)

	# Run make to make the icons
	Popen(["make"], stdout=PIPE).communicate()

	setup_gui()
