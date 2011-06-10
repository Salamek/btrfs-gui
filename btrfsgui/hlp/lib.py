# -*- coding: utf-8 -*-

"""Exceptions and other library functions and classes
"""

import os
import os.path
import stat

class HelperException(Exception):
	def __init__(self, msg, value=500):
		self.message = msg
		self.rv = value
