# -*- coding: utf-8 -*-

from tkinter import *
from tkinter.ttk import *

import btrfsgui.requester

COLOURS = { "Plain": ("#ffff00", "#00ffff"),
			"RAID0": ("#ff0000", "#0000ff"),
			"DUP": ("#ff7f00", "#007fff"),
			"RAID1": ("#7f0000", "#00007f"),
			"RAID10": ("#bf7f00", "#007f7f"),
			}

class UsageDisplay(Frame, btrfsgui.requester.Requester):
	"""Panel displaying usage statistics on a filesystem.
	"""

	def __init__(self, parent):
		Frame.__init__(self, parent)
		# Requester is a mixin, and requires no __init__

		self.create_widgets()

	def create_widgets(self):
		self.columnconfigure(len(COLOURS), weight=1)

		sty = Style()
		for i, (name, (used, free)) in enumerate(iter(COLOURS.items())):
			lbl = Label(self, text=name)
			lbl.grid(column=i, row=0)

			sty.configure("Swatch0{0}.TLabel".format(i),
						  #padding=5, bd=1,
						  bg="#000"#used#, fg=0,
						  #height=20, width=20, padx=10, pady=10)
						  )
			swatch = Label(self, style="Swatch0{0}.TLabel".format(i))
			swatch.grid(sticky=N+S+E+W, column=i, row=1)
			#swatch.grid_propagate(0)

			#sty.configure("Swatch1{0}.TFrame".format(i),
			#			  padding=5, bd=1,
			#			  bg=free, fg=0,
			#			  height=20, width=20, padx=10, pady=10)
			#swatch = Frame(self, style="Swatch1{0}.TFrame".format(i))
			#swatch.grid(sticky=N+S+E+W, column=i, row=2)
			#swatch.grid_propagate(0)

		lbl = Label(self, text="Used")
		lbl.grid(column=len(COLOURS), row=1, sticky=N+S+W)
		lbl = Label(self, text="Allocated")
		lbl.grid(column=len(COLOURS), row=2, sticky=N+S+W)

	def set_display(self, fs):
		"""Pass parameters for the basic FS information so that we
		know how to get the relevant information from the helper.
		"""
		self.fs = fs
