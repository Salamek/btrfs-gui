# -*- coding: utf-8 -*-

"""Global operations, not tied to any one filesystem: scanning
"""

import subprocess
import json
import sys
import os.path

from btrfsgui.hlp.lib import HelperException

SEARCH_PATH = (os.environ["PATH"].split(os.pathsep)
			   + [ "/usr/local/sbin",
				   "/usr/local/bin",
				   "/sbin",
				   "/bin",
				   "/usr/sbin",
				   "/usr/bin",
				   "." ])
_found_btrfs = None

def scan(parameters):
	global _found_btrfs

	devnull = open(os.devnull, "w")

	if _found_btrfs is None:
		_found_btrfs = find_btrfs_binary()

	scanner = subprocess.call([_found_btrfs, "device", "scan"],
							  stderr=subprocess.STDOUT, stdout=devnull)
	if scanner != 0:
		raise HelperException("Couldn't run btrfs dev scan")
	scandata = subprocess.Popen([_found_btrfs, "filesystem", "show"],
								stderr=devnull, stdout=subprocess.PIPE).stdout

	fslist = []
	for line in scandata:
		line = line.decode()
		if line.startswith("Label:"):
			tmp, label, tmp, uuid = line.split()
			if label == "none":
				label = None
			else:
				label = label[1:-1] # Strip surrounding '' from the label
			sys.stderr.write("Helper: found label {0}, UUID {1}\n".format(label, uuid))
			volumes = []
			fslist.append({"label": label, "uuid": uuid, "vols": volumes})
			continue

		line = line.strip()
		if line.startswith("devid"):
			spl = line.split()
			sys.stderr.write("Helper: found dev {0[1]} = {0[7]}\n".format(spl))
			volumes.append({"id": int(spl[1]), "path": spl[7]})
			continue

	sys.stdout.write(json.dumps(fslist))
	sys.stdout.write("\n")

def find_btrfs_binary():
	"""Run through a path to find the btrfs binary
	"""
	for d in SEARCH_PATH:
		command = os.path.join(d, "btrfs")
		if os.path.exists(command):
			return command
	raise HelperException("btrfs command not found in path {0}".format(":".join(SEARCH_PATH)))
