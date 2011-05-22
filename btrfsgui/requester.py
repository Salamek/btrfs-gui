# -*- coding: utf-8 -*-

import json

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

	def request(self, req):
		"""Send a request, parse the result stream in file object f,
		and return the data correctly.
		"""
		ret = None

		self.comms.stdin.write(req)
		self.comms.stdin.flush()

		while True:
			line = self.comms.stdout.readline()
			if line.startswith("OK") or line.startswith("ERR"):
				tmp, rv, message = line.split(None, 2)
				break
			try:
				ret = json.loads(line)
			except ValueError:
				return (599, "Unparsable data", None)
		return (rv, message, ret)

	def request_array(self, req):
		"""Send a requrest, parse repeated lines of output in file
		object f, and return the data correctly.
		"""
		self.comms.stdin.write(req)
		self.comms.stdin.flush()

		def ret():
			while True:
				line = self.comms.stdout.readline()
				if line.startswith("OK"):
					return
				if line.startswith("ERR"):
					tmp, code, message = line.split(None, 2)
					raise RequesterException(code, message)
				try:
					data = json.loads(line)
				except ValueError:
					raise RequesterException(599, "Unparsable data")
				yield data

		return (100, "Not immediately fatal", ret())
