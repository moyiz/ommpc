# OMMPC
*Oh My MPC* is a MPD client module that simply wraps the MPD protocol.
*OMMPC* can be used to control your MPD server with python.

### Why?
For no reason actually. I wanted to learn a thing or two about MPD, and I was like: "what the hell".

### Installation
OMMPC is simply one module. You can install it manually or via setup.py.

```sh
$ git clone https://github.com/moyiz/ommpc.git
$ cd ommpc
$ python2 setup.py install
```

### Usage
A simple playback toggle.

```
from ommpc import OMMPClient

client = OMMPClient()
client.connect()
status = client.commands.status()[0]
if status['state'] == 'play':
    client.commands.pause()
else:
    client.commands.play()
client.disconnect()
```
For more examples, look in the repository.

### Tips
Watching the command list:
```
from ommpc import Commands
print Commands.commands_dict
```
Arguments for a specific command can be found using the commands_dict, or help() on the specific command. Example:
```
from ommpc import OMMPClient
client = OMMPClient()
help(client.commands.playlistinfo)
```
Or using `?` (in ipython)
```
from ommpc import OMMPClient
client = OMMPClient()
client.commands.playlistinfo?
```
### Version
0.1

### License
BSD
