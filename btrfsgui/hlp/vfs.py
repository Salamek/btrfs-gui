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
	"""Return a listing of all the block devices in /dev
	"""
	devs = {}
	for path, dirs, files in os.walk("/dev"):
		# FIXME: delete all .dirs in-place from the dirs list

		lastdir = os.path.basename(path)
		for f in files:
			if f.startswith("."):
				continue

			fullname = os.path.join(path, f)
			try:
				stats = os.stat(fullname)
			except OSError:
				continue
			if not stat.S_ISBLK(stats.st_mode):
				continue

			dev = devs.setdefault(stats.st_rdev,
								  {"rdev": stats.st_rdev,
								   "alias": [],
								   })
			if not os.path.islink(fullname):
				dev["cname"] = fullname
			dev["alias"].append(fullname)

			if lastdir == "by-id":
				dev["by-id"] = fullname
			if lastdir == "by-label":
				dev["by-label"] = fullname
			if lastdir == "by-path":
				dev["by-path"] = fullname
			if lastdir == "by-uuid":
				dev["by-uuid"] = fullname
			if path == "/dev/mapper":
				vgname = []
				lvname = None
				for frag in f.split("--"):
					if frag.find("-") != -1:
						if lvname is not None:
							sys.stderr.write("Malformed LVM device name {0}: ignoring LVM metadata\n".format(f))
							break
						vgtail, lvhead = frag.split("-")
						vgname.append(vgtail)
						lvname = [lvhead]
					elif lvname is None:
						vgname.append(frag)
					else:
						lvname.append(frag)
				if lvname is not None:
					dev["lv"] = "-".join(lvname)
					dev["vg"] = "-".join(vgname)
				else:
					sys.stderr.write("LVM device name with no apparent LV part {0}: ignoring LVM metadata\n".format(f))

	for dev in devs.values():
		sys.stdout.write(json.dumps(dev))
		sys.stdout.write("\n")
		sys.stdout.flush()
