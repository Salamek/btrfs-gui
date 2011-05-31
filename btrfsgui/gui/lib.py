# -*- coding: utf-8 -*-

"""Library of assorted GUI functions
"""

from tkinter import *
from tkinter.ttk import *
import tkinter.messagebox

_icon_warned = False

def image_or_blank(file):
	"""Find and return a tkinter image that can be used as an icon
	"""
	global _icon_warned
	try:
		return PhotoImage(file=file)
	except:
		print("Could not find icon file {0}.".format(file))
		if not _icon_warned:
			tkinter.messagebox.showinfo("Missing icons", "Some icons are missing. You may need to run make in the btrfs-gui source directory to build or download them.")
			_icon_warned = True
		return PhotoImage()
