__author__ = 'moyiz'
__doc__ = """
This script will forward its arguments as commands to MPD.
For example:

mpc_for_shell.py play
mpc_for_shell.py pause
mpc_for_shell.py next
mpc_for_shell.py previous

And so on.
"""

import sys
from ommpc import OMMPClient


def forward_mpd(mpd_server, mpd_port, command, args):
    client = OMMPClient(server=mpd_server, port=mpd_port)
    client.connect()
    client.commands.__getattr__(command)(*args)
    client.disconnect()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print __doc__
        sys.exit(1)
    command, args = sys.argv[1], sys.argv[2:]
    forward_mpd("localhost", 6600, command, args)
