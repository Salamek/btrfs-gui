# -*- coding: utf-8 -*-

"""Functions dealing with determining the sizes of things
"""

import sys
import fcntl
import array
import struct
import json

import mount

BTRFS_IOC_SPACE_INFO = 0xc0109414L

def df(params, state):
	"""Collect information on the usage of the filesystem. Replicate
	the operation of btrfs fi df to start with.
	"""
	uuid = params.split()[0]
	mount.mount(uuid)
	fsfd = mount.fd(uuid)

	# Get the number of spaces we need to allocate for the result
	ret = array.array("B", [0] * 16) # Space for two __u64s
	rv = fcntl.ioctl(fsfd, BTRFS_IOC_SPACE_INFO, ret)
	space_slots, total_spaces = struct.unpack("QQ", ret)

	# Now allocate it, and get the data
	ret = array.array("B", [0] * (16 + 24*total_spaces))
	struct.pack_into("QQ", ret, 0, total_spaces, 0)
	rv = fcntl.ioctl(fsfd, BTRFS_IOC_SPACE_INFO, ret)
	fsfd.close()

	# Parse the result
	space_slots, total_spaces = struct.unpack_from("QQ", ret, 0)

	res = []
	for offset in xrange(16, 16 + 24 * total_spaces, 24):
		flags, total, used = struct.unpack_from("QQQ", ret, offset)
		res.append({"flags": flags, "total": total, "used": used})

	sys.stdout.write(json.dumps(res))
	sys.stdout.write("\n")
