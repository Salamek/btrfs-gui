# -*- coding: utf-8 -*-

from tkinter import *
from tkinter.ttk import *
import collections

from btrfsgui.requester import Requester

COLOURS = collections.OrderedDict(
	[("Single", ("#ffff00", "#00ffff", "#000000")),
	 ("RAID0", ("#ff0000", "#0000ff", "#000000")),
	 ("DUP", ("#ff7f00", "#007fff", "#000000")),
	 ("RAID1", ("#7f0000", "#00007f", "#000000")),
	 ("RAID10", ("#bf7f00", "#007f7f", "#000000")),
	 ])

DF_BOX_PADDING = 20
DF_BOX_WIDTH = 400
DF_BOX_HEIGHT = 50

BTRFS_BLOCK_GROUP_DATA = 1 << 0
BTRFS_BLOCK_GROUP_SYSTEM = 1 << 1
BTRFS_BLOCK_GROUP_METADATA = 1 << 2
BTRFS_BLOCK_GROUP_RAID0 = 1 << 3
BTRFS_BLOCK_GROUP_RAID1 = 1 << 4
BTRFS_BLOCK_GROUP_DUP = 1 << 5
BTRFS_BLOCK_GROUP_RAID10 = 1 << 6

def fade(col):
	rgb = [int(col[1:3], 16), int(col[3:5], 16), int(col[5:7], 16)]
	rgb = [128+int(x/2) for x in rgb]
	return "#{0:x}{1:x}{2:x}".format(*rgb)

class SplitBox(object):
	"""Represents a rectangular area, split either horizontally or
	vertically in given ratios, with coloured segments between each
	split. The segments may themselves be SplitBoxes, with the
	alternative orientation.

	May be iterated over to deliver the indivdual rectangles that need
	to be drawn.
	"""

	HORIZONTAL=0
	VERTICAL=1

	class _Iter(object):
		def __init__(self, box):
			self.box = box
			self.pos = -1
			self.subiter = None

		def __iter__(self):
			return self

		def __next__(self):
			while True:
				if self.subiter is None:
					self.pos += 1
				if self.pos >= len(self.box.divisions):
					raise StopIteration()
				if isinstance(self.box.data[self.pos], SplitBox):
					if self.subiter is None:
						self.subiter = iter(self.box.data[self.pos])
					try:
						rv = self.subiter.next()
						return rv
					except StopIteration:
						self.subiter = None
				else:
					return (self.box.rectangle(self.pos),
							self.box.data[self.pos])

		next = __next__

	def __init__(self, divisions=None, data=None, orient=HORIZONTAL):
		self.divisions = divisions
		self.data = data
		self.orient = orient

		if self.divisions is None:
			self.divisions = []

		if self.data is None:
			self.data = []

		self.total = 0
		for div in self.divisions:
			self.total += div

	def set_position(self, xoffset, yoffset, width, height):
		"""Called after setting all data for this box, to propagate
		the width/height settings down to all levels of the box
		structure.
		"""
		self.xoffset = xoffset
		self.yoffset = yoffset
		self.width = width
		self.height = height
		self.offset = []
		self.dist = []

		if self.orient == self.HORIZONTAL:
			off = self.xoffset
			size = self.width
		else:
			off = self.yoffset
			size = self.height

		for div, dat in zip(self.divisions, self.data):
			dist = size * div / self.total
			if isinstance(dat, SplitBox):
				if self.orient == self.HORIZONTAL:
					dat.set_position(off, self.yoffset, dist, self.height)
				else:
					dat.set_position(self.xoffset, off, self.width, dist)
			self.offset.append(off)
			self.dist.append(dist)
			off += dist

	def rectangle(self, i):
		"""Return the (x0, y0, w, h) tuple of the ith rectangle.
		"""
		if self.orient == self.HORIZONTAL:
			return (self.offset[i], self.yoffset,
					self.dist[i], self.height)
		else:
			return (self.xoffset, self.offset[i],
					self.width, self.dist[i])

	def __len__(self):
		return len(self.divisions)

	def __getitem__(self, i):
		return (self.divisions[i], self.data[i])

	def __setitem__(self, i, v):
		self.total -= self.divisions[i]
		self.divisions[i], self.data[i] = v
		self.total += self.divisions[i]

	def __delitem__(self, i):
		self.total -= self.divisions[i]
		del self.divisions[i]
		del self.data[i]

	def append(self, v):
		self.total += v[0]
		self.divisions.append(v[0])
		self.data.append(v[1])

	def __iter__(self):
		return SplitBox._Iter(self)

class UsageDisplay(Frame, Requester):
	"""Panel displaying usage statistics on a filesystem.
	"""

	def __init__(self, parent, comms):
		Frame.__init__(self, parent)
		Requester.__init__(self, comms)

		self.create_widgets()

	def create_widgets(self):
		self.columnconfigure(len(COLOURS), weight=1)
		self.rowconfigure(1, minsize=30)
		self.rowconfigure(2, minsize=30)

		sty = Style()
		for i, (name, (meta, data, sys)) in enumerate(iter(COLOURS.items())):
			lbl = Label(self, text=name)
			lbl.grid(column=i, row=0)

			sty.configure("Swatch0{0}.TFrame".format(i),
						  background=meta,
						  borderwidth=1)
			swatch = Frame(self, style="Swatch0{0}.TFrame".format(i))
			swatch.grid(sticky=N+S+E+W, column=i, row=1, padx=10, pady=3)

			sty.configure("Swatch1{0}.TFrame".format(i),
						  background=data,
						  borderwidth=1)
			swatch = Frame(self, style="Swatch1{0}.TFrame".format(i))
			swatch.grid(sticky=N+S+E+W, column=i, row=2, padx=10, pady=3)

			self.columnconfigure(i, minsize=50, pad=4)

		lbl = Label(self, text="Data")
		lbl.grid(column=len(COLOURS), row=1, sticky=N+S+W)
		lbl = Label(self, text="Metadata")
		lbl.grid(column=len(COLOURS), row=2, sticky=N+S+W)

		box = LabelFrame(self, text="Data replication and allocation")
		box.grid(sticky=N+S+E+W, row=3, column=0, columnspan=len(COLOURS)+1)
		box.columnconfigure(2, weight=1)
		self.df_display = Canvas(box,
								 width=DF_BOX_WIDTH+2*DF_BOX_PADDING,
								 height=DF_BOX_HEIGHT+2*DF_BOX_PADDING)
		self.df_display.grid(sticky=N+S+E+W, columnspan=3)

		self.df_selection = StringVar()
		Label(box, text="Show unallocated space").grid(row=1, column=0)
		but = Radiobutton(
			box, text="Allocated only",
			variable=self.df_selection,
			value="alloc")
		but.bind("<ButtonRelease-1>", lambda e: self.update_display())
		but.grid(row=1, column=1, sticky=W)
		but = Radiobutton(
			box, text="As raw space",
			variable=self.df_selection,
			value="raw")
		but.bind("<ButtonRelease-1>", lambda e: self.update_display())
		but.grid(row=2, column=1, sticky=W)
		self.df_selection.set("alloc")

	def set_display(self, fs):
		"""Pass parameters for the basic FS information so that we
		know how to get the relevant information from the helper.
		"""
		self.fs = fs
		self.update_display()

	def update_display(self):
		# Clean up the existing display
		self.df_display.delete("all")
		self.df_display.create_rectangle(
			DF_BOX_PADDING-1, DF_BOX_PADDING-1,
			DF_BOX_PADDING+DF_BOX_WIDTH, DF_BOX_PADDING+DF_BOX_HEIGHT,
			width=1, fill="#00ff00", tags=("all", "outline"))

		# Get the allocation and usage of all the block group types
		rv, text, obj = self.request("df {0[uuid]}\n".format(self.fs))
		data = SplitBox(orient=SplitBox.VERTICAL)
		meta = SplitBox(orient=SplitBox.VERTICAL)
		sys = SplitBox(orient=SplitBox.VERTICAL)
		for bg_type in obj:
			if bg_type["flags"] & BTRFS_BLOCK_GROUP_DATA:
				destination = data
				col = 0
			if bg_type["flags"] & BTRFS_BLOCK_GROUP_METADATA:
				destination = meta
				col = 1
			if bg_type["flags"] & BTRFS_BLOCK_GROUP_SYSTEM:
				destination = sys
				col = 2

			if bg_type["flags"] & BTRFS_BLOCK_GROUP_RAID0:
				typ = "RAID0"
			elif bg_type["flags"] & BTRFS_BLOCK_GROUP_RAID1:
				typ = "RAID1"
			elif bg_type["flags"] & BTRFS_BLOCK_GROUP_RAID10:
				typ = "RAID10"
			elif bg_type["flags"] & BTRFS_BLOCK_GROUP_DUP:
				typ = "DUP"
			else:
				typ = "Single"

			usedfree = SplitBox(orient=SplitBox.HORIZONTAL)
			usedfree.append((bg_type["used"],
							 { "fill": COLOURS[typ][col] }))
			usedfree.append((bg_type["size"]-bg_type["used"],
							 { "fill": COLOURS[typ][col], "stripe": fade(COLOURS[typ][col]) }))
			destination.append((usedfree.total, usedfree))
		
		# total is our whole block
		# *_total are the three main divisions
		box = SplitBox(orient=SplitBox.HORIZONTAL)
		print("System total:", sys.total)
		box.append((sys.total, sys))
		print("Meta total:", meta.total)
		box.append((meta.total, meta))
		print("Data total:", data.total)
		box.append((data.total, data))

		box.set_position(DF_BOX_PADDING, DF_BOX_PADDING,
						 DF_BOX_WIDTH, DF_BOX_HEIGHT)
		for rect, data in box:
			rx0 = int(rect[0])
			ry0 = int(rect[1])
			rx1 = int(rect[0]+rect[2])
			ry1 = int(rect[1]+rect[3])
			#print("Rectangle at", rect, rect[0]+rect[2], rx1, rect[1]+rect[3], ry1)

			self.df_display.create_rectangle(
				rx0, ry0, rx1, ry1,
				width=0, tags=("all"), fill=data["fill"])
			if "stripe" in data:
				for x in range(4, int(rect[2]+rect[3]), 8):
					x0 = rx0 + x
					y0 = ry0
					x1 = rx0
					y1 = ry0 + x

					if x0 > rx1:
						y0 += x0 - rx1
						x0 = rx1
					if y1 > ry1:
						x1 += y1 - ry1
						y1 = ry1

					self.df_display.create_line(
						x0, y0, x1, y1,	fill=data["stripe"],
						tags=("all", "stripes"))
