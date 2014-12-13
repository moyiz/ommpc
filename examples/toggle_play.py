__author__ = 'moyiz'
__doc__ = """
Toggles the state of the MPD server.
It will pause the playback if it is playing, otherwise, try to play.
"""
from ommpc import OMMPClient


def toggle_play():
    client = OMMPClient()
    client.connect()
    status = client.commands.status()[0]
    if status['state'] == 'play':
        client.commands.pause()
    else:
        client.commands.play()


if __name__ == "__main__":
    toggle_play()