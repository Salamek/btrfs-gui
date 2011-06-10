# -*- coding: utf-8 -*-

from optparse import OptionParser

from btrfsgui.sudo import init_root_process
from btrfsgui.gui import Application

def main():
	parser = OptionParser()
	parser.add_option("-R", "--remote", action="store", dest="ssh",
					  metavar="<host>",
					  help="Run on the remote system <host>")
	parser.add_option("-s", "--sudo", action="store", dest="sudo_helper",
					  metavar="<cmd>",
					  help="Use <cmd> for gaining root privileges")
	parser.add_option("-H", "--helper", action="store", dest="helper",
					  metavar="<path>", default="btrfs-gui-helper",
					  help="Location of the root-helper to use")
	parser.add_option("--force-root", action="store_true", default=False,
					  dest="force_root",
					  help="Run the GUI as root anyway")
	(options, args) = parser.parse_args()

	subproc = init_root_process(options)
	app = Application(subproc, options)
	app.mainloop()
