# -*- coding: utf-8 -*-

"""Main GUI application code: define and manage the top-level window
"""

from tkinter import *
from tkinter.ttk import *

from btrfsgui.gui.lib import image_or_blank, ScrolledTreeview
from btrfsgui.gui.usagedisplay import UsageDisplay
from btrfsgui.gui.subvolumes import Subvolumes
from btrfsgui.gui.mkfs import MkfsDialog
from btrfsgui.gui.devices import DeviceListDialogue
from btrfsgui.requester import Requester, ex_handler

class Application(Frame, Requester):
	def __init__(self, comms, options):
		Frame.__init__(self, None)
		Requester.__init__(self, comms)

		self.options = options
		self.selected_fs = None

		self.grid(sticky=N+S+E+W)
		self.set_styles()
		self.create_widgets()
		self.master.title("btrfs GUI")

	def set_styles(self):
		self.style = style = Style()

	def create_widgets(self):
		top = self.winfo_toplevel()
		top.geometry("800x600")
		# Set up for a resizable main window
		top.rowconfigure(0, weight=1)
		top.columnconfigure(0, weight=1)
		self.rowconfigure(0, weight=1)
		self.columnconfigure(0, weight=1)

		self.LRpane = PanedWindow(self, orient=HORIZONTAL)
		self.LRpane.grid(sticky=N+S+E+W)

		self.sidebar = PanedWindow(self.LRpane, orient=VERTICAL)
		self.LRpane.add(self.sidebar)
		self.datapane = Notebook(self.LRpane)
		self.LRpane.add(self.datapane)

		fs_frame = Frame(self.sidebar)
		fs_frame.rowconfigure(1, weight=1)
		fs_frame.columnconfigure(0, weight=1)
		Label(fs_frame, text="Filesystems").grid(sticky=W)
		self.fs_list_pos = IntVar()
		fsl_frame, self.fs_list = ScrolledTreeview(
			fs_frame,
			columns=["", "UUID"])
		self.fs_list.heading("#0", text="Filesystem", anchor="w")
		self.fs_list.heading("UUID", text="UUID", anchor="w")
		fsl_frame.grid(sticky=N+S+E+W)
		self.sidebar.add(fs_frame)
		self.fs_list.bind("<Double-Button-1>", self.select_fs)
		self.fs_list.bind("<Button-3>", self.fs_context_menu)

		self.images = { "fs": image_or_blank(file="img/fs_icon.gif"),
						"fs-sel": image_or_blank(file="img/fs_icon_open.gif"),
						"dev": image_or_blank(file="img/disk_icon.gif"), }
		self.fs_list.tag_configure("fs", image=self.images["fs"])
		self.fs_list.tag_configure("dev", image=self.images["dev"])

		self.usage = UsageDisplay(self.datapane, self.comms)
		self.datapane.add(self.usage, text="Space Usage", sticky="nsew")
		self.subvols = Subvolumes(self.datapane, self.comms)
		self.datapane.add(self.subvols, text="Subvolumes", sticky="nsew")

		self.create_menus(top)

		self.update_idletasks()
		self.LRpane.sashpos(0, 150)

	def create_menus(self, top):
		# Set up the main menu
		self.main_menu = Menu(top, tearoff=0)
		top["menu"] = self.main_menu

		# Filesystems menu
		self.file_menu = Menu(self.main_menu, tearoff=0)
		self.file_menu.add_command(label="Scan for filesystems",
								   accelerator="Ctrl-Shift-S",
								   command=self.scan)
		self.file_menu.add_command(label="New Filesystem",
								   command=self.new_filesystem)
		self.file_menu.add_separator()
		self.file_menu.add_command(label="Quit", accelerator="Ctrl-Q",
								   command=self.quit_all)
		
		self.bind_all("<Control-KeyPress-q>", lambda x: self.quit_all())
		self.bind_all("<Control-KeyPress-S>", lambda x: self.scan())

		self.main_menu.add_cascade(label="Filesystems", menu=self.file_menu)

		# Top-level menus provided by the various tab objects
		for w in self.datapane.tabs():
			try:
				self.nametowidget(w).create_top_menus(self.main_menu)
			except AttributeError:
				pass

	def select_fs(self, event):
		"""Select a filesystem by double-clicking on it, or any of its
		devices
		"""
		rowid = self.fs_list.identify_row(event.y)
		if rowid.find(":") != -1:
			rowid = self.fs_list.parent(rowid)
		for afs in self.filesystems:
			if afs["uuid"] == rowid:
				self.set_selected(afs)
				break

	def set_selected(self, fs):
		"""Set the given selection in the UI
		"""
		self.selected_fs = None

		for afs in self.filesystems:
			# The row ID is the UUID of the filesystem
			if afs["uuid"] == fs["uuid"]:
				self.selected_fs = afs
				self.fs_list.item(afs["uuid"], image=self.images["fs-sel"])
			else:
				self.fs_list.item(afs["uuid"], image=self.images["fs"])

		for w in self.datapane.tabs():
			self.nametowidget(w).set_selected(self.selected_fs)

	def new_filesystem(self):
		"""Create a new filesystem
		"""
		win = MkfsDialog(self, self.comms)
		if win.result:
			self.scan()

	@ex_handler
	def scan(self):
		self.fs_list.delete(*self.fs_list.get_children())
		rv, text, obj = self.request("scan")
		self.filesystems = obj

		for fs in obj:
			lbl = fs["label"]
			if lbl is None:
				lbl = "(unlabelled)"
			iid = self.fs_list.insert(
				"", "end",
				iid=fs["uuid"],
				text=lbl,
				values=(fs["uuid"],),
				tags=["fs",],
				image=self.images["fs"])

			fs["vols"].sort(key=lambda x: x["path"])
			for vol in fs["vols"]:
				iid = self.fs_list.insert(
					fs["uuid"], "end",
					iid="{0}:{1}".format(fs["uuid"], vol["id"]),
					text=vol["path"],
					tags=["dev",],
					image=self.images["dev"])

		if self.selected_fs is not None:
			self.set_selected(self.selected_fs)
		else:
			if obj:
				self.set_selected(obj[0])

	def quit_all(self):
		self.quit()

	def fs_context_menu(self, ev):
		"""Work out what in the fs list the user right-clicked on, and
		pop up a suitable context menu for it.
		"""
		rowid = self.fs_list.identify_row(ev.y)
		if rowid == "":
			return

		ctx_menu = Menu(self, tearoff=False)

		if rowid.find(":") != -1:
			# User clicked on a device
			fsid = self.fs_list.parent(rowid)
			devid = rowid.split(":", 1)[1]
			device = self.fs_list.item(rowid, "text")
			ctx_menu.add_command(
				label="Remove",
				command=lambda: self.remove_device(fsid, device))
		else:
			# User clicked on a filesystem
			ctx_menu.add_command(
				label="Add device",
				command=lambda: self.add_device(rowid))

		ctx_menu.bind("<FocusOut>", lambda e: ctx_menu.unpost())
		ctx_menu.post(ev.x_root, ev.y_root)
		ctx_menu.focus_set()

	@ex_handler
	def remove_device(self, fsid, device):
		"""Remove a device from a filesystem
		"""
		# FIXME: Check whether there's an obvious fail on disk size
		# and stop the user from doing it.
		rv, text, obj = self.request("rm_dev", fsid, device)

	@ex_handler
	def add_device(self, fsid):
		"""Add a device to a filesystem
		"""
		# Open up a dialogue window and do the work inside that
		dialogue = DeviceListDialogue(self, self.comms)
		if dialogue.result is not None:
			devname = dialogue.result[0]["cname"]
			rv, text, obj = self.request("add_dev", fsid, devname)
