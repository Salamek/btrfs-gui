# -*- coding: utf-8 -*-

"""btrfs constants and structure definitions
"""

import struct

MINUS_ONE = 0xffffffffffffffff
MINUS_ONE_L = 0xffffffff

# ioctl numbers
IOC_SPACE_INFO = 0xc0109414
IOC_TREE_SEARCH = 0xd0009411

# Object IDs
DEV_ITEMS_OBJECTID = 1
EXTENT_TREE_OBJECTID = 2
CHUNK_TREE_OBJECTID = 3
DEV_TREE_OBJECTID = 4
FS_TREE_OBJECTID = 5
ROOT_TREE_DIR_OBJECTID = 6
CSUM_TREE_OBJECTID = 7
ORPHAN_OBJECTID = -5
TREE_LOG_OBJECTID = -6
TREE_LOG_FIXUP_OBJECTID = -7
TREE_RELOC_OBJECTID = -8
DATA_RELOC_TREE_OBJECTID = -9
EXTENT_CSUM_OBJECTID = -10
FREE_SPACE_OBJECTID = -11
MULTIPLE_OBJECTIDS = -255
FIRST_FREE_OBJECTID = 256
LAST_FREE_OBJECTID = -256
FIRST_CHUNK_TREE_OBJECTID = 256
DEV_ITEMS_OBJECTID = 1
BTREE_INODE_OBJECTID = 1
EMPTY_SUBVOL_DIR_OBJECTID = 2

# Item keys
INODE_ITEM_KEY = 1
INODE_REF_KEY =	12
XATTR_ITEM_KEY = 24
ORPHAN_ITEM_KEY = 48
DIR_LOG_ITEM_KEY = 60
DIR_LOG_INDEX_KEY = 72
DIR_ITEM_KEY = 84
DIR_INDEX_KEY = 96
EXTENT_DATA_KEY = 108
EXTENT_CSUM_KEY = 128
ROOT_ITEM_KEY = 132
ROOT_BACKREF_KEY = 144
ROOT_REF_KEY = 156
EXTENT_ITEM_KEY = 168
TREE_BLOCK_REF_KEY = 176
EXTENT_DATA_REF_KEY = 178
EXTENT_REF_V0_KEY = 180
SHARED_BLOCK_REF_KEY = 182
SHARED_DATA_REF_KEY = 184
BLOCK_GROUP_ITEM_KEY = 192
DEV_EXTENT_KEY = 204
DEV_ITEM_KEY = 216
CHUNK_ITEM_KEY = 228
STRING_ITEM_KEY = 253

# ioctl structures
ioctl_space_args = struct.Struct("=2Q")
ioctl_space_info = struct.Struct("=3Q")
ioctl_search_key = struct.Struct("=Q6QLLL4x32x")
ioctl_search_header = struct.Struct("=3Q2L")

# Internal data structures
dev_item = struct.Struct("<3Q3L3QL2B16s16s")
dev_extent = struct.Struct("<4Q16s")
chunk = struct.Struct("<4Q3L2H")
stripe = struct.Struct("<2Q16s")
block_group_item = struct.Struct("<3Q")

def format_uuid(id):
	return "{0:02x}{1:02x}{2:02x}{3:02x}-{4:02x}{5:02x}-{6:02x}{7:02x}-{8:02x}{9:02x}-{10:02x}{11:02x}{12:02x}{13:02x}{14:02x}{15:02x}".format(*struct.unpack("16B", id))
