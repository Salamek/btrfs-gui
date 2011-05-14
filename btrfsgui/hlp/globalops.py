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
