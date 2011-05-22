# -*- coding: utf-8 -*-

"""Functions dealing with subvolumes
"""

import sys
import fcntl
import array
import struct
import json
import itertools
import os.path

from mount import Filesystem
import btrfsgui.btrfs as btrfs
import btrfsgui.helper

def local_path(fs, tree, inode):
	"""Return the full path (as a list of names) of the object with
	the given inode number in the given FS tree.
	"""
	rv = []
	buf = btrfs.sized_array()
	while inode != 256:
		items = btrfs.search(fs,
							 tree,
							 inode, btrfs.INODE_REF_KEY,
							 buf=buf,
							 structure=btrfs.inode_ref)
		if not items:
			raise btrfsgui.helper.HelperException(
				"Item {0} in tree {1} has no INODE_REF".format(inode, tree))

		header, raw_data, data = items[0]
		index, name_len = data
		inode = header[2] # offset of the key is the objid of the parent
		name = struct.unpack_from("{0}s".format(name_len),
								  raw_data,
								  btrfs.inode_ref.size)[0]
		rv.append(name)

	rv.reverse()
	return rv

def sv_list(params):
	"""List all the subvolumes on the filesystem.
	"""
	uuid = params[0]
	res = {}
	with Filesystem(uuid) as fsfd:
		# Find all trees in the tree of tree roots
		min_tree = btrfs.FIRST_FREE_OBJECTID
		min_key = 0
		buf = btrfs.sized_array()
		while True:
			items = btrfs.search(fsfd,
								 btrfs.ROOT_TREE_OBJECTID,
								 (min_tree, btrfs.MINUS_ONE),
								 (min_key, 255),
								 buf=buf,
								 structure=btrfs.root_ref)
			if not items:
				break
			while items:
				item = {}
				header, raw_data, data = items.pop(0)
				min_tree = sv_id = header[1]
				min_key = found_key = header[3]

				min_key += 1
				if min_key >= 256:
					min_tree += 1
					min_key = 0

				if header[3] != btrfs.ROOT_BACKREF_KEY:
					continue
				sv_parent_subvol = header[2]

				dirid, sequence, name_len = data
				name = struct.unpack_from("{0}s".format(name_len),
										  raw_data,
										  btrfs.root_ref.size)[0]

				item["name"] = name
				item["id"] = sv_id
				item["parent"] = sv_parent_subvol
				# Get the path of this subvolume within its parent
				item["sv_path"] = local_path(fsfd, sv_parent_subvol, dirid)
				res[sv_id] = item

		# Reconstruct the full subvolume path in each case
		for sv_id, data in res.items():
			parent_id = data["parent"]
			data["full_path"] = data["sv_path"]
			while parent_id != btrfs.FS_TREE_OBJECTID:
				data["full_path"] = res[parent_id]["sv_path"] \
									+ [res[parent_id]["name"],] \
									+ data["full_path"]
				parent_id = res[parent_id]["parent"]

	sys.stdout.write(json.dumps(res))
	sys.stdout.write("\n")

def sv_del(params):
	"""Delete a subvolume, by ID.
	"""
	uuid, sv_path = params
	with Filesystem(uuid) as fs:
		# We don't use the fs object as a file descriptor here, but
		# just as a place to open subdirs from
		where = os.path.dirname(sv_path)
		fd = fs.open(where)
		subv_name = os.path.basename(sv_path)

		buf = btrfs.sized_array()
		# pack_into fills any unused space with zero bytes. Since
		# we're selecting PATH_NAME_MAX bytes, there's always at least
		# one byte remaining for a zero terminator

		# FIXME: throw an error if len(subv_name) >
		# btrfs.PATH_NAME_MAX, because it'll do Bad Things.
		btrfs.ioctl_vol_args.pack_into(buf, 0,
									   0, subv_name[:btrfs.PATH_NAME_MAX])
		fcntl.ioctl(fd, btrfs.IOC_SNAP_DESTROY, buf)

def sv_make(params):
	"""Create a subvolume
	"""
	uuid, sv_path = params
	with Filesystem(uuid) as fs:
		where = os.path.dirname(sv_path)
		fd = fs.open(where)
		subv_name = os.path.basename(sv_path)

		buf = btrfs.sized_array()
		btrfs.ioctl_vol_args.pack_into(buf, 0,
									   0, subv_name[:btrfs.PATH_NAME_MAX])
		fcntl.ioctl(fd, btrfs.IOC_SUBVOL_CREATE, buf)
