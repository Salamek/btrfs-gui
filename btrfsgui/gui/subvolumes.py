# -*- coding: utf-8 -*-

from tkinter import *
from tkinter.ttk import *
import tkinter.messagebox
import tkinter.simpledialog
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
							  accelerator="Ctrl-N",
							  command=self.create_subvolume)
		self.menu.add_command(label="Snapshot",
							  accelerator="Ctrl-S")
		self.menu.add_command(label="Delete",
							  command=self.delete_subvolume)
		parent.add_cascade(label="Subvolume", menu=self.menu)

		self.bind_all("<Control-KeyPress-n>", lambda e: self.create_subvolume())

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

	def create_subvolume(self):
		"""Show a directory tree, and create a subvolume in it.
		"""
		ask = NewSubvolume(self, self.fs["uuid"])
		if ask.result:
			self.change_display()

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

		self.sv_list.insert("", "end", text="@", iid="@", values=["0", ""], open=True)
		for subv in sorted(self.subvols.values(), key=lambda x: len(x["full_path"])):
			self.sv_list.insert(
				"@",
				"end",
				text=subv["name"],
				iid=subv["id"],
				values=[subv["id"], os.path.join(*(subv["full_path"] + [subv["name"]]))],
				open=True)


class NewSubvolume(tkinter.simpledialog.Dialog):
	"""Show a directory/subvolume listing of the filesystem, and ask
	for a filename for a new subvolume.
	"""
	def __init__(self, parent, uuid):
		self.uuid = uuid
		self.result = False
		tkinter.simpledialog.Dialog.__init__(self, parent)

	def apply(self):
		"""Process the data in this dialog
		"""
		item = self.file_list.focus()
		path = self.file_list.set(item, "path")
		rv, msg, data = self.parent.request("sub_make {0} {1}\n".format(
			self.uuid, os.path.join(path, self.name.get())))
		if int(rv) == 200:
			self.result = True

	def body(self, master):
		"""Create the dialog body
		"""
		master.columnconfigure(1, weight=1)
		master.rowconfigure(0, weight=1)
		self.file_list = Treeview(master, columns=["path"], displaycolumns=[])
		self.file_list.insert("", "end",
							  text="@",
							  iid="@",
							  values=["."],
							  open=True)
		self.populate_dir("@", ".")
		self.file_list.bind("<<TreeviewOpen>>", self.opened_dir)
		self.file_list.grid(sticky=N+S+E+W, padx=8, pady=8, columnspan=2)

		Label(master, text="New subvolume:")\
					  .grid(row=1, column=0, padx=8, pady=8)
		self.name = StringVar()
		Entry(master, textvariable=self.name)\
					  .grid(row=1, column=1, padx=8, pady=8)
		
		self.bind("<Return>", self.ok)
		self.bind("<Escape>", self.cancel)

	def validate(self):
		"""Check that the data in the dialog is sane. We put few
		limitations on the name: it's not empty, it doesn't contain a
		directory separator character, and it's not too long.
		"""
		name = self.name.get()
		if name == "":
			tkinter.messagebox.showerror(message="Subvolume name must not be empty")
			return False
		if "/" in name:
			tkinter.messagebox.showerror(message="Subvolume name cannot contain /")
			return False
		if len(name) > btrfs.PATH_NAME_MAX:
			tkinter.messagebox.showerror(message="Subvolume name too long")
			return False
		return True

	def populate_dir(self, parentid, dirname):
		"""Populate the tree node at parentid with the contents of the
		directory dirname
		"""
		ret, text, data = self.parent.request_array("ls -dir {0} {1}\n".format(self.uuid, dirname))
		if dirname == ".":
			dirname = ""
		self.file_list.set_children(parentid)
		for item in data:
			extra = ""
			if item["inode"] == 256:
				extra = " **"
			iid = self.file_list.insert(parentid, "end",
										text=item["name"]+extra,
										values=[os.path.join(dirname,
															 item["name"])],
										open=False)
			self.file_list.insert(iid, "end", text="")

	def opened_dir(self, ev):
		"""The user has opened up a tree node, and so we must populate
		it with its contents, if any
		"""
		item = self.file_list.focus()
		path = self.file_list.set(item, "path")
		self.populate_dir(item, path)
