# -*- coding: utf-8 -*-

"""Handling of all root-privilege operations.
"""

# There should be nothing outside this module or the helper code that
# requires root privileges

import sys
import os
import subprocess

def init_root_process(params):
	"""Initialise a co-process that runs as root, and which we can
	communicate with to talk to the FS directly.
	"""
	pthshell = ":".join(["/sbin", "/bin", "/usr/sbin", "/usr/bin",
						 "/usr/local/sbin", "/usr/bin", "."])
	cmd = [ "/bin/sh", "-c",
			"PATH=$PATH:{0}; {1}".format(pthshell, params.helper) ]

	# sh -c "PATH=$PATH:$MYPATH; btrfs-gui-helper"
	# sudo sh -c "PATH=$PATH:$MYPATH; btrfs-gui-helper"
	# ssh remotebox sh -c "PATH=$PATH:$MYPATH; btrfs-gui-helper"
	# ssh remotebox sudo sh -c "PATH=$PATH:$MYPATH; btrfs-gui-helper"

	if os.geteuid() != 0:
		if params.sudo_helper:
			cmd[0:0] = params.sudo_helper.split(" ")
		else:
			sys.stderr.write("Can't run without privileges: run through sudo, or use --sudo\n")
			sys.exit(1)

	if params.ssh:
		cmd[0:0] = ["ssh"] + params.ssh.split(" ")

	subproc = subprocess.Popen(
		cmd, universal_newlines=True,
		stdin=subprocess.PIPE, stdout=subprocess.PIPE)

	if os.geteuid() == 0:
		# We're root already -- see if we know where we came from via
		# sudo, and can drop back to the ordinary user permanently
		if "SUDO_GID" in os.environ:
			os.setuid(int(os.environ["SUDO_GID"]))
		elif not params.force_root:
			# We can't -- bomb out with an error
			sys.stderr.write("This GUI must not be run as root. Use --force-root to override\n")
			sys.exit(1)

	line = subproc.stdout.readline()
	if line.startswith("ERR"):
		print("Couldn't start root helper. Aborted")
		sys.exit(1)

	return subproc
