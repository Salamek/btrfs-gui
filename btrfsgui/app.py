# -*- coding: utf-8 -*-

"""Main GUI application code: define and manage the top-level window
"""

from tkinter import *
from tkinter.ttk import *

import btrfsgui.usagedisplay
import btrfsgui.requester

class Application(Frame, btrfsgui.requester.Requester):
	def __init__(self, comms, options):
		Frame.__init__(self, None)
		btrfsgui.requester.Requester.__init__(self, comms)

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
		self.datapane = Frame(self.LRpane)
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

		self.usage = btrfsgui.usagedisplay.UsageDisplay(self.datapane)
		self.usage.grid(sticky=N+S+E+W)

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

	def scan(self):
		rv, text, obj = self.request("scan\n")
		self.fs_list.set_children("")

		for fs in obj:
			lbl = fs["label"]
			if lbl is None:
				lbl = "(unlabelled)"
			iid = self.fs_list.insert(
				"", "end",
				iid=fs["uuid"],
				text=lbl,
				values=(fs["uuid"],))

			fs["vols"].sort(key=lambda x: x["path"])
			for vol in fs["vols"]:
				iid = self.fs_list.insert(
					fs["uuid"], "end",
					iid=fs["uuid"]+":"+vol["id"],
					text=vol["path"])

		self.usage.set_display(obj[0])

	def quit_all(self):
		self.request("quit\n")
		self.quit()
