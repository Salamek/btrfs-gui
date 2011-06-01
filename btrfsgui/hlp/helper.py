# -*- coding: utf-8 -*-

import sys
import traceback
import os

import btrfsgui.hlp.globalops
import btrfsgui.hlp.vfs
import btrfsgui.hlp.size
import btrfsgui.hlp.subvol
from btrfsgui.hlp.lib import HelperException

def quit_all(params):
	sys.exit(0)

def main():
	"""Run a R-E-P loop."""

	if os.geteuid() != 0:
		sys.stdout.write("ERR 550 Root helper not running as root\n")
		sys.stdout.flush()
		sys.exit(1)
	else:
		sys.stdout.write("OK 200 Ready\n")
		sys.stdout.flush()

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
			sys.stdout.write("ERR 550 Root helper exception: {0}\n".format(ex))
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
	"scan": btrfsgui.hlp.globalops.scan,
	"df": btrfsgui.hlp.size.df,
	"vol_df": btrfsgui.hlp.size.volume_df,
	"sub_list": btrfsgui.hlp.subvol.sv_list,
	"sub_del": btrfsgui.hlp.subvol.sv_del,
	"sub_make": btrfsgui.hlp.subvol.sv_make,
	"sub_snap": btrfsgui.hlp.subvol.sv_snap,
	"sub_def": btrfsgui.hlp.subvol.sv_def,
	"ls": btrfsgui.hlp.vfs.ls,
	}
