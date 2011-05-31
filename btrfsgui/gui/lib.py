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


"""Scrolled helpers shamelessly lifted from Frederik Lundh at
http://effbot.org/zone/tkinter-scrollbar-patterns.htm
"""
def Scrolled(_widget, _master, _mode='y', **options):
	frame = Frame(_master, relief=SUNKEN)
	frame.rowconfigure(0, weight=1)
	frame.columnconfigure(0, weight=1)

	widget = _widget(frame, **options)
	widget.grid(row=0, column=0, sticky=N+S+E+W)

	xscrollbar = yscrollbar = None
	if 'x' in _mode:
		xscrollbar = Scrollbar(frame, orient=HORIZONTAL)
		widget.config(xscrollcommand=xscrollbar.set)
		xscrollbar.config(command=widget.xview)
		xscrollbar.grid(row=1, column=0, sticky=E+W)
	if 'y' in _mode:
		yscrollbar = Scrollbar(frame)
		widget.config(yscrollcommand=yscrollbar.set)
		yscrollbar.config(command=widget.yview)
		yscrollbar.grid(row=0, column=1, sticky=N+S)
	return (frame, widget)

def ScrolledTreeview(master, _mode='y', **options):
	return Scrolled(Treeview, master, _mode, **options)

def ScrolledListbox(master, _mode='y', **options):
	return Scrolled(Listbox, master, _mode, **options)

def ScrolledText(master, _mode='y', **options):
	return Scrolled(Text, master, _mode, **options)

def ScrolledCanvas(master, _mode='xy', **options):
	return Scrolled(Canvas, master, _mode, **options)
