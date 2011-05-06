# -*- coding: utf-8 -*-

"""Main GUI application code: define and manage the top-level window
"""

from tkinter import *
from tkinter.ttk import *
import json

class Requester(object):
	"""Mixin class for classes which make requests of the root-level
	helper process. Flush requests, parse return values, and the like.
	"""
	def __init__(self, comms):
		self.comms = comms

	def request(self, req):
		"""Send a request, parse the result stream in file object f,
		and return the data correctly.
		"""
		ret = None

		self.comms.stdin.write(req)
		self.comms.stdin.flush()

		while True:
			line = self.comms.stdout.readline()
			if line.startswith("OK") or line.startswith("ERR"):
				tmp, rv, message = line.split(None, 2)
				break
			try:
				ret = json.loads(line)
			except ValueError:
				return (599, "Unparsable data", None)
		return (rv, message, ret)

	def request_array(self, req):
		"""Send a requrest, parse repeated lines of output in file
		object f, and return the data correctly.
		"""
		ret = []

		self.comms.stdin.write(req)
		self.comms.stdin.flush()

		while True:
			line = self.comms.stdout.readline()
			if line.startswith("OK") or line.startswith("ERR"):
				tmp, rv, message = line.split(None, 2)
				break
			try:
				ret.append(json.loads(line))
			except ValueError:
				return (599, "Unparsable data", None)
		return (rv, message, ret)


class Application(Frame, Requester):
	def __init__(self, comms, options):
		Frame.__init__(self, None)
		Requester.__init__(self, comms)

		self.options = options

		self.grid(sticky=N+S+E+W)
		self.create_widgets()
		self.master.title("btrfs GUI")

	def create_widgets(self):
		top = self.winfo_toplevel()
		top.geometry("800x600")
		# Set up for a resizable main window
		top.rowconfigure(0, weight=1)
		top.columnconfigure(0, weight=1)
		self.rowconfigure(0, weight=1)
		self.columnconfigure(0, weight=1)

		style = Style()
		style.configure("Debug.TPanedwindow", background="#f00")
		style.configure("Debug.TFrame", background="#0f0")

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
		
		self.bind_all("<Control-KeyPress-q>", self.quit_all)
		self.bind_all("<Control-Shift-KeyPress-s>", self.scan)

		self.main_menu.add_cascade(label="Filesystems", menu=self.file_menu)

	def scan(self):
		rv, text, obj = self.request("scan\n")
		self.fs_list.set_children("")

		for fs in obj:
			self.fs_list.insert("", "end", iid=fs["uuid"], text=fs["label"],
								values=(fs["uuid"],))
			self.fs_list.insert(fs["uuid"], 0, iid="BLANK")

	def quit_all(self):
		self.request("quit\n")
		self.quit()
