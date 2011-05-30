# -*- coding: utf-8 -*-

from tkinter import *
from tkinter.ttk import *
import tkinter.messagebox
import tkinter.simpledialog
import os.path

from btrfsgui.gui.lib import image_or_blank
from btrfsgui.requester import Requester, ex_handler
import btrfsgui.btrfs as btrfs

class MkfsDialog(tkinter.simpledialog.Dialog, Requester):
	"""Show options for making a filesystem
	"""
	def __init__(self, parent, comms):
		self.result = False
		self.devices = []
		Requester.__init__(self, comms)
		tkinter.simpledialog.Dialog.__init__(self, parent)

	@ex_handler
	def apply(self):
		"""Process the data in this dialog
		"""
		pass

	def body(self, master):
		"""Create the dialog body
		"""
		self.rowconfigure(1, weight=0)
		self.rowconfigure(0, weight=1)
		master.columnconfigure(1, weight=1)
		master.rowconfigure(3, weight=1)
		minfo = master.grid_info()
		minfo["sticky"] = N+S+E+W
		master.grid(**minfo)

		frm = LabelFrame(master, text="Label")
		Label(frm, text="Label:")\
			.grid(row=0, column=0)
		self.label = StringVar()
		Entry(frm, textvariable=self.label)\
			.grid(row=0, column=1)
		frm.grid(row=0, column=0, sticky=N+S+E+W,
				 ipadx=4, ipady=4, padx=4, pady=4)

		frm = LabelFrame(master, text="Replication")
		Label(frm, text="Data").grid(row=0, column=1, padx=4)
		Label(frm, text="Metadata").grid(row=0, column=2, padx=4)
		self.data_profile = StringVar()
		self.meta_profile = StringVar()
		self.data_profile.set("Single")
		self.meta_profile.set("RAID-1")
		self.dbuttons = {}
		self.mbuttons = {}
		for i, lbl in enumerate(("Single", "RAID-0", "RAID-1", "RAID-10")):
			Label(frm, text=lbl).grid(row=i+1, column=0, sticky=W, padx=4)
			self.dbuttons[lbl] = Radiobutton(frm, value=lbl,
											 variable=self.data_profile)
			self.dbuttons[lbl].grid(row=i+1, column=1)
			self.mbuttons[lbl] = Radiobutton(frm, value=lbl,
											 variable=self.meta_profile)
			self.mbuttons[lbl].grid(row=i+1, column=2)
		self.buttons_valid()
		frm.grid(row=1, column=0, sticky=N+S+E+W,
				 padx=4, pady=4, ipadx=4, ipady=4)

		frm = LabelFrame(master, text="Options")
		self.mixed = IntVar()
		Checkbutton(frm, text="Mixed data/metadata", variable=self.mixed)\
			.grid(row=0, column=0, padx=4, pady=4)
		frm.grid(row=2, column=0, sticky=N+S+E+W, padx=4, pady=4)

		frm = LabelFrame(master, text="Devices")
		frm.columnconfigure(4, weight=1)
		self.device_list = Treeview(frm)
		self.device_list.grid(columnspan=5, sticky=N+S+E+W, padx=4, pady=4)
		self.device_filter = StringVar()
		self.device_filter.set("dev")
		Radiobutton(frm, text="All", command=self.fill_device_list,
					variable=self.device_filter, value="all")\
					.grid(row=1, column=0, padx=4, pady=4)
		Radiobutton(frm, text="/dev", command=self.fill_device_list,
					variable=self.device_filter, value="dev")\
					.grid(row=1, column=1, padx=4, pady=4)
		Radiobutton(frm, text="By ID", command=self.fill_device_list,
					variable=self.device_filter, value="id")\
					.grid(row=1, column=2, padx=4, pady=4)
		Radiobutton(frm, text="By UUID", command=self.fill_device_list,
					variable=self.device_filter, value="uuid")\
					.grid(row=1, column=3, padx=4, pady=4)
		Radiobutton(frm, text="By path", command=self.fill_device_list,
					variable=self.device_filter, value="path")\
					.grid(row=1, column=4, padx=4, pady=4)
		frm.grid(row=0, column=1, sticky=N+S+E+W, padx=4, pady=4, rowspan=4)

		self.bind("<Escape>", self.cancel)
		self.fill_device_list()

	def buttons_valid(self):
		"""Enable/disable the buttons according to which options are
		possible
		"""
		if len(self.devices) < 4:
			state = ["disabled"]
		else:
			state = ["!disabled"]
		self.dbuttons["RAID-10"].state(state)
		self.mbuttons["RAID-10"].state(state)

		if len(self.devices) < 2:
			state = ["disabled"]
		else:
			state = ["!disabled"]
		self.dbuttons["RAID-0"].state(state)
		self.mbuttons["RAID-0"].state(state)
		self.dbuttons["RAID-1"].state(state)

	@ex_handler
	def fill_device_list(self):
		"""Fill the list of available devices
		"""
		# Clear the existing list
		self.device_list.delete(*self.device_list.get_children())

		for dev in self.devices:
			self.device_list.insert("", "end", text="* " + dev["fullname"])

		# Ask the root helper for a filtered list of devices, based on
		# our options
		cmd = ["ls_blk"]
		if self.device_filter.get() == "all":
			cmd.append("-r")
		path = { "all": "/dev",
				 "dev": "/dev",
				 "id": "/dev/disk/by-id",
				 "uuid": "/dev/disk/by-uuid",
				 "path": "/dev/disk/by-path" }[self.device_filter.get()]
		cmd.append(path)

		rv, message, items = self.request_array(*cmd)
		for dev in sorted(list(items), key=lambda x: x["fullname"]):
			pos = "end"
			if dev in self.devices:
				continue
			self.device_list.insert("", "end", text=dev["fullname"])

	def validate(self):
		"""Check that the data in the dialog is sane.
		"""
		pass
