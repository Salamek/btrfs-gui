# -*- coding: utf-8 -*-

"""Library of assorted GUI functions
"""

from tkinter import *
from tkinter.ttk import *

def image_or_blank(file):
	"""Find and return a tkinter image that can be used as an icon
	"""
	try:
		return PhotoImage(file=file)
	except:
		print("Could not find icon file {0}. You may need to run make.".format(file))
		return PhotoImage()
