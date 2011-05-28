# -*- coding: utf-8 -*-

import json
import tkinter.messagebox

class RequesterException(Exception):
	def __init__(self, msg, value=500):
		self.message = msg
		self.rv = value

class Requester(object):
	"""Mixin class for classes which make requests of the root-level
	helper process. Flush requests, parse return values, and the like.
	"""
	def __init__(self, comms):
		self.comms = comms

	def request(self, *parts):
		"""Send a request, parse the result stream in file object f,
		and return the data correctly.
		"""
		ret = None

		req = " ".join([str(p).replace("\\", "\\\\").replace(" ", "\\ ")
						for p in parts])

		self.comms.stdin.write(req)
		self.comms.stdin.write("\n")
		self.comms.stdin.flush()

		while True:
			line = self.comms.stdout.readline()
			if line.startswith("OK"):
				tmp, rv, message = line.split(None, 2)
				break
			elif line.startswith("ERR"):
				tmp, rv, message = line.split(None, 2)
				raise RequesterException(message, rv)
			try:
				ret = json.loads(line)
			except ValueError:
				raise RequesterException("Unparsable data", 599)
		return (rv, message, ret)

	def request_array(self, *parts):
		"""Send a requrest, parse repeated lines of output in file
		object f, and return the data correctly.
		"""
		req = " ".join([str(p).replace("\\", "\\\\").replace(" ", "\\ ")
						for p in parts])

		self.comms.stdin.write(req)
		self.comms.stdin.write("\n")
		self.comms.stdin.flush()

		def ret():
			while True:
				line = self.comms.stdout.readline()
				if line.startswith("OK"):
					return
				if line.startswith("ERR"):
					tmp, code, message = line.split(None, 2)
					raise RequesterException(message, code)
				try:
					data = json.loads(line)
				except ValueError:
					raise RequesterException("Unparsable data", 599)
				yield data

		return (100, "Not immediately fatal", ret())

def ex_handler(fn):
	def hdlr(*args, **kwargs):
		try:
			return fn(*args, **kwargs)
		except RequesterException as rq:
			tkinter.messagebox.showerror("Error", rq.message)
		except IOError as ioe:
			if ioe.errno == 32: # Broken pipe
				tkinter.messagebox.showerror(title="This helper is dead", message="Root helper has stopped unexpectedly. Restart the application to continue.")
			else:
				raise
	return hdlr
