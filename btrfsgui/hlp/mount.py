# -*- coding: utf-8 -*-

"""Operations dealing with mounting and unmounting btrfs filesystems
"""

import os
import os.path
import sys
import subprocess
import tempfile
import atexit

_local_dir = None

class Filesystem(object):
	"""Context manager for opening a filesystem.
	"""
	class _DirFD(object):
		def __init__(self, fd):
			self.fd = fd

		def __str__(self):
			return str(self.fd)

		def fileno(self):
			return self.fd

	def __init__(self, uuid):
		self.uuid = uuid

	def __enter__(self):
		global _local_dir
		mount(self.uuid)
		self.fd = os.open(os.path.join(_local_dir, self.uuid), os.O_DIRECTORY)
		return self._DirFD(self.fd)

	def __exit__(self, exc_type, exc_value, traceback):
		os.close(self.fd)
		# Return false to re-throw any exception in progress as we exit
		return False

@atexit.register
def cleanup():
	"""Global clean-up: unmount _all_ of our temporary files.
	"""
	global _local_dir
	if _local_dir is None:
		return

	for d in os.listdir(_local_dir):
		umount(d, fatal=False)
	try:
		os.rmdir(_local_dir)
	except:
		pass
	_local_dir = None

def mount(uuid):
	"""Mount the filesystem with UUID=uuid, at /<tmp>/<uuid>. This
	allows us to get hold of the filesystem itself, and run ioctls
	against it.

	If the filesystem is already mounted, do nothing.
	"""
	global _local_dir
	if _local_dir is None:
		_local_dir = tempfile.mkdtemp(prefix="btrfs-gui-")
		sys.stderr.write("Helper: Created private directory {0}\n".format(_local_dir))

	dirpath = os.path.join(_local_dir, uuid)
	try:
		os.mkdir(dirpath)
	except OSError, ex:
		if ex.errno == 17: # File exists
			return
		else:
			raise ex
	cmd = ["mount", "-t", "btrfs",
		   "-o", "subvolid=0",
		   "UUID={0}".format(uuid), dirpath]
	subprocess.check_call(cmd)
	sys.stderr.write("Helper: Mounted filesystem UUID={0} at {1}\n".format(uuid, dirpath))

def umount(uuid, fatal=True):
	"""Unmount the filesystem with UUID=<uuid>, and clean up after
	ourselves. If <fatal> is True, then raise exceptions at the
	earliest opportunity. Otherwise, try each step of the process in
	turn, regardless of whether it succeeded or failed.
	"""
	dirpath = os.path.join(_local_dir, uuid)
	cmd = ["umount", dirpath]

	if fatal:
		subprocess.check_call(cmd)
		os.rmdir(dirpath)
	else:
		subprocess.call(cmd)
		try:
			os.rmdir(dirpath)
		except OSError:
			pass

	sys.stderr.write("Helper: Umounted filesystem UUID={0} from {1}\n".format(uuid, dirpath))
