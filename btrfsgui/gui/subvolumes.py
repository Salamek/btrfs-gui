# -*- coding: utf-8 -*-

from tkinter import *
from tkinter.ttk import *
import tkinter.messagebox
import tkinter.simpledialog
import os.path

from btrfsgui.gui.lib import image_or_blank
from btrfsgui.requester import Requester, ex_handler
import btrfsgui.btrfs as btrfs

def current_selection(fn):
	"""Decorator to retrieve and set the current selection and
	pass its details to the decorated method
	"""
	def newfn(self):
		subvid = self.sv_list.selection()[0]
		if subvid == "@":
			vol_path = "."
			vol_id = btrfs.FS_TREE_OBJECTID
		else:
			subv = self.subvols[subvid]
			vol_path = os.path.join(*(subv["full_path"] + [subv["name"],]))
			vol_id = subv["id"]
		fn(self, vol_path, vol_id)
	return newfn

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
							  accelerator="Ctrl-S",
							  command=self.create_snapshot)
		self.menu.add_command(label="Set default",
							  command=self.set_default)
		self.menu.add_command(label="Delete",
							  command=self.delete_subvolume)
		parent.add_cascade(label="Subvolume", menu=self.menu)

		self.bind_all("<Control-KeyPress-n>", lambda e: self.create_subvolume())

	def create_widgets(self):
		self.columnconfigure(0, weight=1)
		self.rowconfigure(0, weight=1)

		self.sv_list = Treeview(self, columns=["name", "id"])
		self.sv_list.heading("#0", text="path", anchor="w")
		self.sv_list.heading("id", text="id", anchor="w")
		self.sv_list.heading("name", text="name", anchor="w")
		self.sv_list.grid(sticky=N+S+W+E)

		self.ctx_menu = Menu(self, tearoff=False)
		self.ctx_menu.add_command(label="Snapshot",
								  command=self.create_snapshot)
		self.ctx_menu.add_command(label="Set default",
								  command=self.set_default)
		self.ctx_menu.add_command(label="Delete",
								  command=self.delete_subvolume)
		self.ctx_menu.bind("<FocusOut>", lambda e: self.ctx_menu.unpost())

		self.sv_list.bind("<Button-3>", self.popup_menu)

		self.img = { "dir": image_or_blank("img/directory.gif"),
					 "subv": image_or_blank("img/subvolume.gif"),
					 "subv-def": image_or_blank("img/subvolume_default.gif"),
					 }

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

	@ex_handler
	def create_subvolume(self):
		"""Show a directory tree, and create a subvolume in it.
		"""
		ask = NewSubvolume(self, self.fs["uuid"])
		if ask.result:
			self.change_display()

	@ex_handler
	@current_selection
	def create_snapshot(self, vol_path, vol_id):
		"""Show a directory tree, and snapshot the current subvolume
		to a user-selected position.
		"""
		ask = NewSubvolume(self, self.fs["uuid"], source=vol_path)
		if ask.result:
			self.change_display()

	@ex_handler
	@current_selection
	def delete_subvolume(self, vol_path, vol_id):
		"""Delete the subvolume selected in the list
		"""
		ok = tkinter.messagebox.askokcancel(
			"Delete subvolume",
			"This will delete the subvolume:\n\n{0}\n\nThis action cannot be undone.".format(vol_path),
			default=tkinter.messagebox.CANCEL,
			icon=tkinter.messagebox.WARNING)
		if ok:
			rv, text, obj = self.request("sub_del", self.fs["uuid"], vol_path)
			self.change_display()

	@ex_handler
	@current_selection
	def set_default(self, vol_path, vol_id):
		"""Set the current selection to be the default subvolume
		"""
		rv, text, obj = self.request("sub_def", self.fs["uuid"], vol_id)
		self.update_display()

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

	@ex_handler
	def update_display(self):
		if not self.stale:
			return

		# Clean up the existing display
		self.sv_list.delete(*self.sv_list.get_children())

		# Get the list of subvolumes, and populate the display
		rv, text, self.subvols = self.request("sub_list", self.fs["uuid"])

		self.sv_list.insert("", "end", text="@", iid="@", values=["0", ""],
							open=True, image=self.img["subv"])

		def_set = False
		for subv in sorted(self.subvols.values(), key=lambda x: len(x["full_path"])):
			path = os.path.join(*(subv["full_path"] + [subv["name"]]))
			img = self.img["subv"]
			if subv.get("default", False):
				def_set = True
				img = self.img["subv-def"]
			self.sv_list.insert(
				"@",
				"end",
				text=path,
				iid=subv["id"],
				values=[subv["name"], subv["id"]],
				open=True,
				image=img)

		if not def_set:
			self.sv_list.item("@", image=self.img["subv-def"])


class NewSubvolume(tkinter.simpledialog.Dialog):
	"""Show a directory/subvolume listing of the filesystem, and ask
	for a filename for a new subvolume.
	"""
	def __init__(self, parent, uuid, source=None):
		self.uuid = uuid
		self.result = False
		self.source = source
		tkinter.simpledialog.Dialog.__init__(self, parent)

	@ex_handler
	def apply(self):
		"""Process the data in this dialog
		"""
		item = self.file_list.focus()
		path = self.file_list.set(item, "path")
		target = os.path.join(path, self.name.get())

		if self.source is None:
			rv, msg, data = self.parent.request(
				"sub_make", self.uuid, target)
		else:
			rv, msg, data = self.parent.request(
				"sub_snap", self.uuid, self.source, target)

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
							  open=True,
							  image=self.parent.img["subv"])
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

	@ex_handler
	def populate_dir(self, parentid, dirname):
		"""Populate the tree node at parentid with the contents of the
		directory dirname
		"""
		ret, text, data = self.parent.request_array("ls", "-dir",
													self.uuid,
													dirname)
		if dirname == ".":
			dirname = ""
		self.file_list.set_children(parentid)
		for item in data:
			extra = ""
			img = self.parent.img["dir"]
			if item["inode"] == 256:
				img = self.parent.img["subv"]
			iid = self.file_list.insert(parentid, "end",
										text=item["name"]+extra,
										values=[os.path.join(dirname,
															 item["name"])],
										open=False,
										image=img)
			self.file_list.insert(iid, "end", text="")

	def opened_dir(self, ev):
		"""The user has opened up a tree node, and so we must populate
		it with its contents, if any
		"""
		item = self.file_list.focus()
		path = self.file_list.set(item, "path")
		self.populate_dir(item, path)
