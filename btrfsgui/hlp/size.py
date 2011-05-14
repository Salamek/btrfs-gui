# -*- coding: utf-8 -*-

"""Functions dealing with determining the sizes of things
"""

import sys
import fcntl
import array
import struct
import json

import mount
import btrfs as btrfs

def sized_array(count):
	return array.array("B", itertools.repeat(0, count))

def search(fd, tree,
		   objid, key_type, offset=[0, btrfs.MINUS_ONE],
		   transid=[0, btrfs.MINUS_ONE], number=btrfs.MINUS_ONE_L,
		   structure=None, buf=None):
	try:
		min_objid, max_objid = objid
	except TypeError:
		min_objid = max_objid = objid
	try:
		min_type, max_type = key_type
	except TypeError:
		min_type = max_type = key_type
	try:
		min_offset, max_offset = offset
	except TypeError:
		min_offset = max_offset = offset
	try:
		min_transid, max_transid = transid
	except TypeError:
		min_transid = max_transid = transid

	if buf is None:
		buf = sized_array(4096)
	btrfs.ioctl_search_key.pack_into(
		buf, 0,
		tree, # Tree
		min_objid, max_objid,		# ObjectID range
		min_offset, max_offset,		# Offset range
		min_transid, max_transid,	# TransID range
		min_type, max_type,			# Key type range
		number						# Number of items
		)

	rv = fcntl.ioctl(fd, btrfs.IOC_TREE_SEARCH, buf)
	results = btrfs.ioctl_search_key.unpack_from(buf, 0)
	num_items = results[9]
	pos = btrfs.ioctl_search_key.size
	ret = []
	while num_items > 0:
		num_items =- 1
		header = btrfs.ioctl_search_header.unpack_from(buf, pos)
		pos += btrfs.ioctl_search_header.size
		raw_data = buf[pos:pos+header[4]]
		data = None
		if structure is not None:
			data = structure.unpack_from(buf, pos)
			#sys.stderr.write("Header claims length is {0}. Header length is {1}, structure length is {2}\n".format(header[4], btrfs.ioctl_search_header.size, structure.size))

		#sys.stderr.write("Found key:\n  header {0}\n  data {1}\n".format(header, data))

		ret.append((header, raw_data, data))
		pos += header[4]

	return ret

def df(params, state):
	"""Collect information on the usage of the filesystem. Replicate
	the operation of btrfs fi df to start with.
	"""
	uuid = params.split()[0]
	mount.mount(uuid)
	fsfd = mount.fd(uuid)

	# Get the number of spaces we need to allocate for the result
	ret = sized_array(16) # Space for two __u64s
	rv = fcntl.ioctl(fsfd, btrfs.IOC_SPACE_INFO, ret)
	space_slots, total_spaces = struct.unpack("QQ", ret)

	# Now allocate it, and get the data
	ret = array.array("B", [0] * (16 + 24*total_spaces))
	struct.pack_into("QQ", ret, 0, total_spaces, 0)
	rv = fcntl.ioctl(fsfd, btrfs.IOC_SPACE_INFO, ret)
	fsfd.close()

	# Parse the result
	space_slots, total_spaces = struct.unpack_from("QQ", ret, 0)

	res = []
	for offset in xrange(16, 16 + 24 * total_spaces, 24):
		flags, total, used = struct.unpack_from("QQQ", ret, offset)
		res.append({"flags": flags, "total": total, "used": used})

	sys.stdout.write(json.dumps(res))
	sys.stdout.write("\n")
