# -*- coding: utf-8 -*-

"""GUI widgets relating to devices
"""

from tkinter import *
from tkinter.ttk import *
import tkinter.messagebox
import tkinter.simpledialog
import os.path
import collections

from btrfsgui.gui.lib import ScrolledTreeview
from btrfsgui.requester import Requester, ex_handler

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
		return self.sel_devices.values()


class DeviceListDialogue(tkinter.simpledialog.Dialog, Requester):
    """Basic device dialogue box for selecting a single block device
    """
    def __init__(self, parent, comms):
        self.result = None
        Requester.__init__(self, comms)
        tkinter.simpledialog.Dialog.__init__(self, parent)

    @ex_handler
    def apply(self):
        """Process the data in this dialogue
        """
        self.result = list(self.devices.selection())

    def body(self, master):
        """Create the dialogue box body
        """
        frm = LabelFrame(master, text="Devices")
        self.devices = DeviceList(frm, self)
        self.devices.grid()
        frm.grid(sticky=N+S+E+W, padx=4, pady=4)

    def validate(self):
        """Check that the selection makes sense
        """
        if len(self.devices.selection()) != 1:
            tkinter.messagebox.showerror(
                "Unexpected selection",
                "Exactly one device should be selected")
            return False

        return True
