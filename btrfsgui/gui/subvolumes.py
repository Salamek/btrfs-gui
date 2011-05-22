# -*- coding: utf-8 -*-

from tkinter import *
from tkinter.ttk import *
import tkinter.messagebox
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

	def create_top_menus(self, parent):
		"""Create menus in the application's menu list
		"""
		self.menu = Menu(parent, tearoff=False)
		self.menu.add_command(label="New subvolume",
							  accelerator="Ctrl-N")
		self.menu.add_command(label="Snapshot",
							  accelerator="Ctrl-S")
		self.menu.add_command(label="Delete",
							  command=self.delete_subvolume)
		parent.add_cascade(label="Subvolume", menu=self.menu)

	def create_widgets(self):
		self.sv_list = Treeview(self, columns=["id", "path"])
		self.sv_list.heading("#0", text="name", anchor="w")
		self.sv_list.heading("id", text="id", anchor="w")
		self.sv_list.heading("path", text="path", anchor="w")
		self.sv_list.grid(sticky=N+S+W+E)

		self.ctx_menu = Menu(self, tearoff=False)
		self.ctx_menu.add_command(label="Snapshot")
		self.ctx_menu.add_command(label="Delete",
								  command=self.delete_subvolume)
		self.ctx_menu.bind("<FocusOut>", lambda e: self.ctx_menu.unpost())

		self.sv_list.bind("<Button-3>", self.popup_menu)

	def popup_menu(self, ev):
		"""Select an item, and pop up the context menu for it
		"""
		row = self.sv_list.identify_row(ev.y)
		self.sv_list.selection_set(row)
		if row != "":
			self.ctx_menu.post(ev.x_root, ev.y_root)
			# Set focus here so that the menu gets <FocusOut> events
			# when the user clicks elsewhere, and we can close the
			# menu properly.
			self.ctx_menu.focus_set()

	def delete_subvolume(self):
		"""Delete the subvolume selected in the list
		"""
		subvid = self.sv_list.selection()[0]
		subv = self.subvols[subvid]
		vol_path = os.path.join(*(subv["full_path"] + [subv["name"],]))
		ok = tkinter.messagebox.askokcancel(
			"Delete subvolume",
			"This will delete the subvolume:\n\n{0}\n\nThis action cannot be undone.".format(vol_path),
			default=tkinter.messagebox.CANCEL,
			icon=tkinter.messagebox.WARNING)
		if ok:
			rv, text, obj = self.request("sub_del {0[uuid]} {1}\n"
										 .format(self.fs, vol_path))
			self.change_display()

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
		rv, text, self.subvols = self.request("sub_list {0[uuid]}\n".format(self.fs))

		self.sv_list.insert("", "end", text="/", iid="/", values=["0", ""], open=True)
		for subv in sorted(self.subvols.values(), key=lambda x: len(x["full_path"])):
			self.sv_list.insert(
				"/",
				"end",
				text=subv["name"],
				iid=subv["id"],
				values=[subv["id"], os.path.join(*(subv["full_path"] + [subv["name"]]))],
				open=True)
