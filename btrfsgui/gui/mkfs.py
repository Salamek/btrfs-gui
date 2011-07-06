# -*- coding: utf-8 -*-

from tkinter import *
from tkinter.ttk import *
import tkinter.messagebox
import tkinter.simpledialog
import os.path
import collections
import json

from btrfsgui.gui.lib import image_or_blank, ScrolledTreeview
from btrfsgui.requester import Requester, ex_handler
import btrfsgui.btrfs as btrfs

REP_TYPES = ("Single", "RAID-0", "RAID-1", "RAID-10")
# Map from display rep types to mkfs parameters
REP_MAP = { "Single": "single",
			"RAID-0": "raid0",
			"RAID-1": "raid1",
			"RAID-10": "raid10",
			}

class MkfsDialog(tkinter.simpledialog.Dialog, Requester):
	"""Show options for making a filesystem
	"""
	def __init__(self, parent, comms):
		self.result = False
		Requester.__init__(self, comms)
		tkinter.simpledialog.Dialog.__init__(self, parent)

	@ex_handler
	def apply(self):
		"""Process the data in this dialog
		"""
		cmd = [ "mkfs" ]
		# List of devices
		cmd.append(json.dumps([d["cname"] for d in self.devices.selection()]))
		# Profiles
		cmd += [ REP_MAP[self.data_profile.get()],
				 REP_MAP[self.meta_profile.get()] ]
		# Additional options
		options = {}
		if self.label.get() != "":
			options["label"] = self.label.get()
		if self.mixed.get():
			options["mixed"] = True
		cmd.append(json.dumps(options))
		# Do the command
		rv, message, items = self.request(*cmd)
		# Indicate success (we don't get to this point if the command
		# failed -- it throws an exception)
		self.result = True

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

		frm = LabelFrame(master, text="Devices")
		frm.columnconfigure(4, weight=1)
		self.devices = DeviceList(frm, self, self.buttons_valid)
		self.devices.grid()
		frm.grid(row=0, column=1, sticky=N+S+E+W, padx=4, pady=4, rowspan=4)

		frm = LabelFrame(master, text="Replication")
		Label(frm, text="Data").grid(row=0, column=1, padx=4)
		Label(frm, text="Metadata").grid(row=0, column=2, padx=4)
		self.data_profile = StringVar()
		self.meta_profile = StringVar()
		self.data_profile.set("Single")
		self.meta_profile.set("RAID-1")
		self.dbuttons = {}
		self.mbuttons = {}
		for i, lbl in enumerate(REP_TYPES):
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

		self.bind("<Escape>", self.cancel)

	def buttons_valid(self):
		"""Enable/disable the buttons according to which options are
		possible. Return value indicates whether the current selection
		is possible.
		"""
		print("Checking buttons valid")
		if len(self.devices.selection()) < 4:
			state = ["disabled"]
		else:
			state = ["!disabled"]
		self.dbuttons["RAID-10"].state(state)
		self.mbuttons["RAID-10"].state(state)

		if len(self.devices.selection()) < 2:
			state = ["disabled"]
		else:
			state = ["!disabled"]
		self.dbuttons["RAID-0"].state(state)
		self.mbuttons["RAID-0"].state(state)
		self.dbuttons["RAID-1"].state(state)

		# Check for disabled/selected states
		for t in REP_TYPES:
			if (self.data_profile == t
				and "disabled" in self.dbuttons[t].state()):
				return False
			if (self.meta_profile == t
				and "disabled" in self.mbuttons[t].state()):
				return False

		return True

	def validate(self):
		"""Check that the data in the dialog is sane. Checks are
		limited: ensure that the RAID levels are feasible with this
		many devices.
		"""
		if not self.buttons_valid():
			tkinter.messagebox.showerror(
				"Incorrect options",
				"Selected replication levels need more devices to build on")
			return False

		return True

class DeviceList(Frame):
	"""List of devices.
	"""
	def __init__(self, parent, requester,
				 update_cb=lambda: True, multiple=False):
		Frame.__init__(self, parent)
		self.requester = requester
		self.update_cb = update_cb

		self.sel_devices = collections.OrderedDict()
		self.all_devices = collections.OrderedDict()

		devfrm, self.device_list = ScrolledTreeview(
			self, columns=("rdev",), displaycolumns=())
		self.device_list.bind("<Double-Button-1>", self._user_selection)
		devfrm.grid(columnspan=5, sticky=N+S+E+W, padx=4, pady=4)
		self.device_filter = StringVar()
		self.device_filter.set("dev")
		Radiobutton(self, text="/dev", command=self.fill_device_list,
					variable=self.device_filter, value="dev")\
					.grid(row=1, column=1, padx=4, pady=4)
		Radiobutton(self, text="By ID", command=self.fill_device_list,
					variable=self.device_filter, value="id")\
					.grid(row=1, column=2, padx=4, pady=4)
		Radiobutton(self, text="By UUID", command=self.fill_device_list,
					variable=self.device_filter, value="uuid")\
					.grid(row=1, column=3, padx=4, pady=4)
		Radiobutton(self, text="By path", command=self.fill_device_list,
					variable=self.device_filter, value="path")\
					.grid(row=1, column=4, padx=4, pady=4)
		Radiobutton(self, text="LVM volumes", command=self.fill_device_list,
					variable=self.device_filter, value="lvm")\
					.grid(row=1, column=4, padx=4, pady=4)
		self.fill_device_list()

	@ex_handler
	def fill_device_list(self):
		"""Fill the list of available devices
		"""
		# Ask the root helper for a filtered list of devices, based on
		# our options
		rv, message, items = self.requester.request_array("ls_blk")

		filt, sortkey = {
			"dev": (lambda x: os.path.dirname(x["cname"]) == "/dev",
					lambda x: x["cname"]),
			"id": (lambda x: "by-id" in x,
				   lambda x: x["by-id"]),
			"uuid": (lambda x: "by-uuid" in x,
					 lambda x: x["by-uuid"]),
			"path": (lambda x: "by-path" in x,
					 lambda x: x["by-path"]),
			"lvm": (lambda x: "lv" in x,
					lambda x: x["vg"] + " : " + x["lv"]),
			}[self.device_filter.get()]

		self.all_devices = collections.OrderedDict()
		for dev in sorted(filter(filt, items), key=sortkey):
			dev["fullname"] = os.path.basename(sortkey(dev))
			self.all_devices[dev["rdev"]] = dev

		self._update_device_list()

	def _update_device_list(self):
		"""Update the list of devices, without calling out to the far end
		"""
		# Clear the existing list
		self.device_list.delete(*self.device_list.get_children())

		# Fill the devices we've selected
		for devid, dev in self.sel_devices.items():
			self.device_list.insert("", "end", text="* " + dev["fullname"],
									values=(dev["rdev"],))

		for devid, dev in self.all_devices.items():
			pos = "end"
			if devid in self.sel_devices:
				continue
			self.device_list.insert("", "end", text=dev["fullname"],
									values=(dev["rdev"],))

	def _user_selection(self, ev):
		"""User has double-clicked on a device: flip between one state
		and another
		"""
		rowid = self.device_list.identify_row(ev.y)
		if rowid == "":
			return
		item = self.device_list.item(rowid)
		devid = item["values"][0]

		if devid in self.sel_devices:
			del self.sel_devices[devid]
		else:
			self.sel_devices[devid] = self.all_devices[devid]

		self.update_cb()
		self._update_device_list()

	def selection(self):
		"""Return the list of selected devices
		"""
		print(self.sel_devices.values())
		return self.sel_devices.values()
