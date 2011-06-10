# -*- coding: utf-8 -*-

"""Virtual filesystem commands: ordinary common functions, such as
listing the contents of a directory, or performing file operations.
"""

import os
import sys
import os.path
import json
import stat

from btrfsgui.hlp.mount import Filesystem

_filters = { "all": lambda s: True,
			 "dir": stat.S_ISDIR,
			 "block": stat.S_ISBLK
			 }

def ls(params):
	"""Return a listing of a directory as multiple objects:

	ls [-<filtername>] <uuid> <path>
	
	Pass . as the path to obtain the root dir listing.
	"""
	if len(params) == 3:
		p, uuid, path = params
		typefilter = _filters[p[1:]]
	else:
		uuid, path = params
		typefilter = _filters["all"]

	# If we don't do this, we get to be able to list the whole host's
	# filesystem
	if path[0] == '/':
		path = path.lstrip("/")

	with Filesystem(uuid) as fs:
		path = fs.fullpath(path)
		for name in os.listdir(path):
			_output_file_details(typefilter, path, name)

def ls_blk(params):
	"""Return a listing of the block devices in a directory
	"""
	recursive = False
	while True:
		p = params.pop(0)
		if p[0] != "-":
			break
		if p == "-r":
			recursive = True
	typefilter = _filters["block"]

	if recursive:
		for path, dirs, files in os.walk(p):
			for f in files:
				_output_file_details(typefilter, path, f)
	else:
		for f in os.listdir(p):
			_output_file_details(typefilter, p, f)

def _output_file_details(typefilter, p, f):
	filename = os.path.join(p, f)
	try:
		stats = os.stat(filename)
	except:
		return
	if not typefilter(stats.st_mode):
		return
	res = { "name": f,
			"path": p,
			"fullname": filename,
			"mode": stats.st_mode,
			"inode": stats.st_ino,
			}
	if stat.S_ISBLK(stats.st_mode) or stat.S_ISCHR(stats.st_mode):
		res["rdev"] = stats.st_rdev

	sys.stdout.write(json.dumps(res))
	sys.stdout.write("\n")
	sys.stdout.flush()
