# -*- coding: utf-8 -*-

"""Global operations, not tied to any one filesystem: scanning
"""

import subprocess
import json
import sys

import btrfsgui.helper

def scan(line, state):
	devnull = open("/dev/null", "w")
	scanner = subprocess.call(["btrfs", "device", "scan"],
							  stderr=subprocess.STDOUT, stdout=devnull)
	if scanner != 0:
		raise btrfsgui.helper.HelperException("Couldn't run btrfs dev scan")
	scandata = subprocess.Popen(["btrfs", "filesystem", "show"],
								stderr=devnull, stdout=subprocess.PIPE).stdout
	fslist = []
	for line in scandata:
		if not line.startswith("Label:"):
			continue
		tmp, label, tmp, uuid = line.split()
		sys.stderr.write("Helper: found label {0}, UUID {1}\n".format(label, uuid))
		fslist.append({"label": label, "uuid": uuid})

	sys.stdout.write(json.dumps(fslist))
	sys.stdout.write("\n")
