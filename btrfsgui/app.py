# -*- coding: utf-8 -*-

"""Main GUI application code: define and manage the top-level window
"""

from Tkinter import *
import json

def get_data(f):
	"""Parse the stream in file object f, and return the data correctly.
	"""
	ret = None
	while True:
		line = f.readline()
		if line.startswith("OK") or line.startswith("ERR"):
			tmp, rv, message = line.split(None, 2)
			break
		try:
			ret = json.loads(line)
		except ValueError:
			return (599, "Unparsable data", None)
	return (rv, message, ret)

def get_data_array(f):
	"""Parse repeated lines of output in file object f, and return the
	data correctly."""
	ret = []
	while True:
		line = f.readline()
		if line.startswith("OK") or line.startswith("ERR"):
			tmp, rv, message = line.split(None, 2)
			break
		try:
			ret.append(json.loads(line))
		except ValueError:
			return (599, "Unparsable data", None)
	return (rv, message, ret)

class Application(Frame):
	def __init__(self, comms, options):
		Frame.__init__(self, None)

		self.comms = comms
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
		self.comms.stdin.write("scan\n")
		self.comms.stdin.flush()
		rv, text, obj = get_data(self.comms.stdout)
		print "GUI: scan result", rv, obj

	def quit_all(self):
		self.comms.stdin.write("quit\n")
		self.comms.stdin.flush()
		self.quit()
