# -*- coding: utf-8 -*-

"""Virtual filesystem commands: ordinary common functions, such as
listing the contents of a directory, or performing file operations.
"""

import os
import sys
import os.path
import json
import stat

from mount import Filesystem
import btrfsgui.helper

_filters = { "all": lambda s: True,
			 "dir": stat.S_ISDIR,
			 "block": lambda s: stat.S_ISDIR(s) or stat.S_ISBLK(s)
			 }

def ls(params):
	"""Return a listing of a directory as multiple objects:

	ls [-<filtername>] <uuid> <path>
	
	Pass . as the path to obtain the root dir listing.
	"""
	if params[0] == '-':
		p, uuid, path = params.split(None, 2)
		typefilter = _filters[p[1:]]
	else:
		uuid, path = params.split(None, 1)
		typefilter = _filters["all"]

	# If we don't do this, we get to be able to list the whole host's
	# filesystem
	if path[0] == '/':
		path = path.lstrip("/")

	with Filesystem(uuid) as fs:
		path = fs.fullpath(path)
		for name in os.listdir(path):
			stats = os.stat(os.path.join(path, name))
			if not typefilter(stats.st_mode):
				continue
			res = { "name": name,
					"mode": stats.st_mode,
					"inode": stats.st_ino,
					}
			if stat.S_ISBLK(stats.st_mode) or stat.S_ISCHR(stats.st_mode):
				res["rdev"] = stats.st_rdev

			sys.stdout.write(json.dumps(res))
			sys.stdout.write("\n")
			sys.stdout.flush()
