# -*- coding: utf-8 -*-

"""Main GUI application code: define and manage the top-level window
"""

from tkinter import *
from tkinter.ttk import *

from btrfsgui.gui.usagedisplay import UsageDisplay
from btrfsgui.gui.subvolumes import Subvolumes
from btrfsgui.requester import Requester

class Application(Frame, Requester):
	def __init__(self, comms, options):
		Frame.__init__(self, None)
		Requester.__init__(self, comms)

		self.options = options

		self.grid(sticky=N+S+E+W)
		self.set_styles()
		self.create_widgets()
		self.master.title("btrfs GUI")

	def set_styles(self):
		self.style = style = Style()
		style.configure("Debug.TPanedwindow", background="#f00")
		style.configure("Debug.TFrame", background="#0f0")
		style.configure("Debug.TLabel", background="#ff0")

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
		fs_frame_label = Label(fs_frame, text="Filesystems")
		fs_frame_label.grid(sticky=N+S+W)
		self.fs_list_pos = IntVar()
		self.fs_list = Treeview(
			fs_frame,
			columns=["", "UUID"])
		self.fs_list.grid(sticky=N+S+E+W)
		self.sidebar.add(fs_frame)
		self.fs_list.bind("<Double-Button-1>", self.select_fs)

		self.images = { "fs": PhotoImage(file="img/fs_icon.gif"),
						"fs-sel": PhotoImage(file="img/fs_icon_open.gif"),
						"dev": PhotoImage(file="img/disk_icon.gif"), }
		self.fs_list.tag_configure("fs", image=self.images["fs"])
		self.fs_list.tag_configure("dev", image=self.images["dev"])

		self.usage = UsageDisplay(self.datapane, self.comms)
		self.datapane.add(self.usage, text="Space Usage", sticky="nsew")
		self.subvols = Subvolumes(self.datapane, self.comms)
		self.datapane.add(self.subvols, text="Subvolumes", sticky="nsew")

		self.create_menus(top)

	def create_menus(self, top):
		# Set up the main menu
		self.main_menu = Menu(top, tearoff=0)
		top["menu"] = self.main_menu

		# Filesystems menu
		self.file_menu = Menu(self.main_menu, tearoff=0)
		self.file_menu.add_command(label="Scan for filesystems",
								   accelerator="Ctrl-Shift-S",
								   command=self.scan)
		self.file_menu.add_separator()
		self.file_menu.add_command(label="Quit", accelerator="Ctrl-Q",
								   command=self.quit_all)
		
		self.bind_all("<Control-KeyPress-q>", lambda x: self.quit_all())
		self.bind_all("<Control-KeyPress-S>", lambda x: self.scan())

		self.main_menu.add_cascade(label="Filesystems", menu=self.file_menu)

	def select_fs(self, event):
		"""Select a filesystem by double-clicking on it, or any of its
		devices
		"""
		rowid = self.fs_list.identify_row(event.y)
		if rowid.find(":") != -1:
			rowid = self.fs_list.parent(rowid)
		# The row ID is the UUID of the filesystem
		for fs in self.filesystems:
			if fs["uuid"] == rowid:
				self.set_selected(fs)
				self.fs_list.item(fs["uuid"], image=self.images["fs-sel"])
			else:
				self.fs_list.item(fs["uuid"], image=self.images["fs"])

	def set_selected(self, fs):
		self.selected_fs = fs
		for w in self.datapane.tabs():
			self.nametowidget(w).set_selected(fs)

	def scan(self):
		rv, text, obj = self.request("scan\n")
		self.fs_list.delete(*self.fs_list.get_children())
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

		self.set_selected(obj[0])

	def quit_all(self):
		self.request("quit\n")
		self.quit()
