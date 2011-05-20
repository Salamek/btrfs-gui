# -*- coding: utf-8 -*-

from tkinter import *
from tkinter.ttk import *
import os.path

from btrfsgui.requester import Requester
import btrfsgui.btrfs as btrfs

class Subvolumes(Frame, Requester):
	"""Panel displaying a filesystem's subvolumes.
	"""

	def __init__(self, parent, comms):
		Frame.__init__(self, parent)
		Requester.__init__(self, comms)

		self.create_widgets()

	def create_widgets(self):
		self.sv_list = Treeview(self, columns=["id", "path"])
		self.sv_list.heading("#0", text="name", anchor="w")
		self.sv_list.heading("id", text="id", anchor="w")
		self.sv_list.heading("path", text="path", anchor="w")
		self.sv_list.grid(sticky=N+S+W+E)

	def set_selected(self, fs):
		"""Pass parameters for the basic FS information so that we
		know how to get the relevant information from the helper.
		"""
		self.fs = fs
		self.stale = True
		self.update_display()

	def change_display(self):
		self.stale = True
		self.update_display()

	def update_display(self):
		if not self.stale:
			return

		# Clean up the existing display
		self.sv_list.delete(*self.sv_list.get_children())

		# Get the list of subvolumes, and populate the display
		rv, text, obj = self.request("sub_list {0[uuid]}\n".format(self.fs))

		self.sv_list.insert("", "end", text="/", iid="/", values=["0", ""], open=True)
		for subv in sorted(obj.values(), key=lambda x: len(x["full_path"])):
			self.sv_list.insert(
				"/",
				"end",
				text=subv["name"],
				iid=subv["id"],
				values=[subv["id"], os.path.join(*(subv["full_path"] + [subv["name"]]))],
				open=True)
