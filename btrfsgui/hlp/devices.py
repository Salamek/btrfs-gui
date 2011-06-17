# -*- coding: utf-8 -*-

"""Functions dealing with the filesystem at the device level: removal,
addition, resize, balancing, monitoring.
"""

import sys
import fcntl
import multiprocessing

from btrfsgui.hlp.mount import Filesystem, cleanup
import btrfsgui.btrfs as btrfs
from btrfsgui.hlp.lib import HelperException

def _rm_dev_async(uuid, devname):
	"""This operation could be insanely long-lived, so we run this in
	a separate process. The use of Filesystem here will (probably)
	generate a second temporary file
	"""
	with Filesystem(uuid) as fsfd:
		buf = btrfs.sized_array()
		btrfs.ioctl_vol_args.pack_into(buf, 0, 0, devname)
		fcntl.ioctl(fsfd, btrfs.IOC_DEV_RM, buf)
	cleanup()

def rm_dev(params):
	"""Remove a device from the FS. This takes a very long time, so
	spawn off a subprocess and run it from that.
	"""
	uuid = params[0]
	devname = params[1]
	proc = multiprocessing.Process(
		target=_rm_dev_async,
		args=(uuid, devname),)
	proc.start()

def add_dev(params):
	"""Add a device to the FS.
	"""
	uuid = params[0]
	devname = params[1]
	with Filesystem(uuid) as fsfd:
		buf = btrfs.sized_array()
		btrfs.ioctl_vol_args.pack_into(buf, 0, 0, devname)
		fcntl.ioctl(fsfd, btrfs.IOC_DEV_ADD, buf)
