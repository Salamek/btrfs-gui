# -*- coding: utf-8 -*-

import sys
import traceback

import hlp.globalops
import hlp.size
import hlp.subvol

class HelperState(object):
	pass

class HelperException(Exception):
	def __init__(self, msg, value=500):
		self.message = msg
		self.rv = value

def quit_all(line, state):
	sys.exit(0)

def open_fs(line, state):
	sys.stderr.write("Helper: Open filesystem {0}\n", line)
	state.fd = os.open(line, O_RDWR)

def close_fs(line, state):
	if state.fd is None:
		raise HelperException("No filesystem open")
	os.close(state.fd)
	state.fd = None

def main():
	"""Run a R-E-P loop."""

	state = HelperState()
	state.fd = None
	
	while True:
		sys.stdin.flush()
		line = sys.stdin.readline()
		line = line[:-1] # Chop off the trailing \n
		if line == "":
			break
		try:
			command, line = line.split(None, 1)
		except ValueError:
			command = line.strip()
			line = ""

		if command not in COMMANDS:
			sys.stdout.write("ERR Command not known\n")
		try:
			COMMANDS[command](line, state)
			sys.stdout.write("OK 200 All good\n")
		except HelperException, ex:
			sys.stdout.write("ERR {0.rv} {0.message}\n".format(ex))
			traceback.print_exc(None, sys.stderr)
		except Exception, ex:
			sys.stdout.write("ERR 550 {0}\n".format(ex))
			traceback.print_exc(None, sys.stderr)
		sys.stdout.flush()

COMMANDS = {
	"quit": quit_all,
	"scan": hlp.globalops.scan,
	"open": open_fs,
	"close": close_fs,
	"df": hlp.size.df,
	"vol_df": hlp.size.volume_df,
	"sub_list": hlp.subvol.sv_list,
	"sub_del": hlp.subvol.sv_del,
	}
