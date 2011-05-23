# -*- coding: utf-8 -*-

import sys
import traceback

import hlp.globalops
import hlp.vfs
import hlp.size
import hlp.subvol

class HelperException(Exception):
	def __init__(self, msg, value=500):
		self.message = msg
		self.rv = value

def quit_all(params):
	sys.exit(0)

def main():
	"""Run a R-E-P loop."""
	
	while True:
		sys.stdin.flush()
		line = sys.stdin.readline()
		line = line[:-1] # Chop off the trailing \n
		if line == "":
			break
		parameters = parse(line)
		command = parameters.pop(0)

		if command not in COMMANDS:
			sys.stdout.write("ERR Command not known\n")
		try:
			COMMANDS[command](parameters)
			sys.stdout.write("OK 200 All good\n")
		except HelperException, ex:
			sys.stdout.write("ERR {0.rv} {0.message}\n".format(ex))
			traceback.print_exc(None, sys.stderr)
		except Exception, ex:
			sys.stdout.write("ERR 550 {0}\n".format(ex))
			traceback.print_exc(None, sys.stderr)
		sys.stdout.flush()

def parse(line):
	"""Parse a line of input into tokens. Tokens are separated by
	spaces.	Characters may be escaped by \
	"""
	state = "space"
	output = []
	it = iter(line)
	for c in it:
		if state == "read":
			if c == " ":
				state = "space"
				continue
			elif c == "\\":
				c = it.next()
			output[-1] += c
		elif state == "space":
			if c != " ":
				state = "read"
				if c == "\\":
					c = it.next()
				output.append(c)
	return output

COMMANDS = {
	"quit": quit_all,
	"scan": hlp.globalops.scan,
	"df": hlp.size.df,
	"vol_df": hlp.size.volume_df,
	"sub_list": hlp.subvol.sv_list,
	"sub_del": hlp.subvol.sv_del,
	"sub_make": hlp.subvol.sv_make,
	"sub_snap": hlp.subvol.sv_snap,
	"ls": hlp.vfs.ls,
	}
