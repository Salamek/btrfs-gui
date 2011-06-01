# -*- coding: utf-8 -*-

"""Functions dealing with determining the sizes of things
"""

import sys
import fcntl
import json

from btrfsgui.hlp.mount import Filesystem
import btrfsgui.btrfs as btrfs
from btrfsgui.hlp.lib import HelperException

def df(params):
	"""Collect information on the usage of the filesystem. Replicate
	the operation of btrfs fi df to start with.
	"""
	uuid = params[0]
	with Filesystem(uuid) as fsfd:
		# Get the number of spaces we need to allocate for the result
		ret = btrfs.sized_array(btrfs.ioctl_space_args.size)
		rv = fcntl.ioctl(fsfd, btrfs.IOC_SPACE_INFO, ret)
		space_slots, total_spaces = btrfs.ioctl_space_args.unpack(ret)

		# Now allocate it, and get the data
		buf_size = (btrfs.ioctl_space_args.size
					+ total_spaces * btrfs.ioctl_space_info.size)
		ret = btrfs.sized_array(buf_size)
		btrfs.ioctl_space_args.pack_into(ret, 0, total_spaces, 0)
		rv = fcntl.ioctl(fsfd, btrfs.IOC_SPACE_INFO, ret)

	# Parse the result
	space_slots, total_spaces = btrfs.ioctl_space_args.unpack_from(ret, 0)

	res = []
	for offset in xrange(btrfs.ioctl_space_args.size,
						 buf_size,
						 btrfs.ioctl_space_info.size):
		flags, total, used = btrfs.ioctl_space_info.unpack_from(ret, offset)
		res.append({"flags": flags, "size": total, "used": used})

	sys.stdout.write(json.dumps(res))
	sys.stdout.write("\n")

def volume_df(params):
	"""Collect usage statistics on a specific volume in the filesystem.
	"""
	uuid, devid = params
	devid = int(devid)

	with Filesystem(uuid) as fsfd:
		# First, collect per-device data for this device
		buf = btrfs.sized_array()
		items = btrfs.search(fsfd,
							 btrfs.CHUNK_TREE_OBJECTID,
							 btrfs.DEV_ITEMS_OBJECTID, btrfs.DEV_ITEM_KEY, devid,
							 number=1,
							 buf=buf,
							 structure=btrfs.dev_item)

		if len(items) > 1:
			raise HelperException("More than one record for this devid!")
		if len(items) < 1:
			raise HelperException("devid not found")

		res = {}
		header, raw_data, data = items[0]

		res["size"] = data[1]
		res["used"] = data[2]
		res["uuid"] = btrfs.format_uuid(data[12])
		res["usage"] = {}

		# Now, collect data on the block group types in use
		last_offset = 0
		while True:
			# Iterate over all chunk extents on this device
			items = btrfs.search(fsfd,
								 btrfs.DEV_TREE_OBJECTID,
								 devid,
								 btrfs.DEV_EXTENT_KEY,
								 (last_offset, btrfs.MINUS_ONE),
								 buf=buf,
								 structure=btrfs.dev_extent)
			if not items:
				break

			while items:
				header, raw_data, ext_data = items.pop(0)

				ext_offset = header[2]
				last_offset = ext_offset+1
			
				chunk_objid = ext_data[1]
				chunk_offset = ext_data[2]
				ext_length = ext_data[3]

				# For each extent on this device, we need to look up what
				# it's a part of
				chunks = btrfs.search(fsfd,
									  btrfs.CHUNK_TREE_OBJECTID,
									  chunk_objid, btrfs.CHUNK_ITEM_KEY, chunk_offset,
									  buf=buf,
									  structure=btrfs.chunk,
									  number=1)
				if len(chunks) != 1:
					raise HelperException("Wrong number of results from searching for a single chunk key ({0})".format(len(chunks)))
				header, raw_data, chunk_info = chunks[0]

				chunk_length = chunk_info[0]
				chunk_type = chunk_info[3]

				# Get the amount of space used in this block group, as well
				extents = btrfs.search(fsfd,
									   btrfs.EXTENT_TREE_OBJECTID,
									   chunk_offset, btrfs.BLOCK_GROUP_ITEM_KEY,
									   buf=buf,
									   structure=btrfs.block_group_item,
									   number=1)
				if len(extents) != 1:
					raise HelperException("Wrong number of results from searching for a single extent key ({0})".format(len(extents)))
				header, raw_data, extent_info = extents[0]

				if header[2] != chunk_length:
					raise HelperException("Chunk length inconsistent: chunk tree says {0} bytes, extent tree says {1} bytes".format(chunk_length, header[2]))
				chunk_used = extent_info[0]
													  
				if chunk_type not in res["usage"]:
					res["usage"][chunk_type] = {
						"flags": chunk_type,
						"size": 0,
						"used": 0,
						}
				res["usage"][chunk_type]["size"] += ext_length
				# We have a total of chunk_used space used, out of
				# chunk_length in this block group. So
				# chunk_used/chunk_length is the proportion of the BG
				# used. We multiply that by the length of the dev_extent
				# to get the amount of space used in the dev_extent.
				res["usage"][chunk_type]["used"] += chunk_used * ext_length / chunk_length

	sys.stdout.write(json.dumps(res))
	sys.stdout.write("\n")
