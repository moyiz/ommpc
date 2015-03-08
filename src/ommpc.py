__author__ = 'moyiz'
__doc__ = """
Oh My MPC is a MPD client module that simply wraps the MPD protocol.
OMMPC can be used to control your MPD server with python, and can be
used to implement your own MPD client.


Basic Usage (Simple Playback Toggle):
===================================
from ommpc import OMMPClient

client = OMMPClient()
client.connect()
status = client.commands.status()[0]
if status['state'] == 'play':
    client.commands.pause()
else:
    client.commands.play()
client.disconnect()


To see the command list:
========================
from ommpc import Commands
print Commands.commands_dict

Each command has a __doc__ parameter, to show the arguments it receives.
I tried to keep the documentation as clear as possible.
For documentation about the mpd commands, visit the official reference:
http://www.musicpd.org/doc/protocol/command_reference.html
"""
import socket


class OMMPClient(object):
    """
    Manages a connection to a mpd server.

    Example:
    ========
    client = OMMPClient()
    client.connect()
    client.commands.play()
    client.disconnect()

    Will start playing whatever in the current playlist
    """

    def __init__(self, server="localhost", port=6600, password=None):
        """
        :param server: Name or IP address of the mpd server host (default: localhost)
        :type server: str
        :param port: Port used by the mpd server (default: 6600)
        :type port: int
        :param password: The password for the MPD server
        :type password: str
        """
        self._con = _Connection(server, port)
        self.commands = self._command_wrapper(Commands)
        self._password = password

    def connect(self):
        """
        Initiates the connection
        """
        self._con.connect()
        result = self._con.receive()
        if self._password:
            p = self.commands.password(self._password)
            if Parser.OK_MSG not in p:
                return p
        return result

    def disconnect(self):
        """
        Disconnects nicely
        """
        self.commands.close()
        self._con.disconnect()

    def _recv(self):
        """
        Receives all data until 'OK' or 'ACK'
        :return: data received from server
        :rtype: str
        """
        result = self._con.receive()
        if result.startswith(Parser.NOT_OK_MSG) or len(result) == 0:
            return result
        while not result.endswith(Parser.OK_MSG + '\n') and not result.startswith(Parser.OK_MSG):
            result += self._con.receive()
        return result

    def _command_wrapper(self, cls):
        """
        A wrapper for the Commands class, used to make commands to be sent
        instead of to be returned.
        """
        def command_send(func, args):
            self._con.send(func(*args))
            result = self._recv()
            if len(result) == 0:  # Reconnect if no results were received
                self._con.connect()
                self._recv()
                return command_send(func, args)
            parsed_result = Parser.parse(result)
            if not parsed_result:
                raise MPDCommandError("Wrong command usage or insufficient permissions: {}".format(result))
            return parsed_result

        class Wrapper(cls):
            """
            The actual class that wraps Commands
            It generates new functions to each of Commands attributes, and all it does is to wrap
            Commands attributes with command_send.
            """
            def __init__(self):
                pass

            def __getattr__(self, item):
                not_wrapped = cls.__getattr__(item)

                def f(*args):
                    return command_send(not_wrapped, args)

                f.__doc__ = not_wrapped.__doc__
                f.__name__ = not_wrapped.__name__
                return f

        return Wrapper()


class _Connection(object):
    """
    Implements the connection itself
    """

    def __init__(self, host, port):
        self._conn = (host, port)
        self._sock = None

    def connect(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect(self._conn)

    def disconnect(self):
        """
        Closes the connection
        """
        self._sock.close()

    def send(self, data):
        """
        Sends data if socket exists
        """
        if self._sock is None:
            raise ConnectionError("Error: a connection was not initiated, use 'connect' first.")
        self._sock.send(data)

    def receive(self, max_bytes=4096):
        """
        Receives data from the socket.
        :param max_bytes - maximum amount of data to receive (default: 4096)
        :type max_bytes - int
        """
        if self._sock is None:
            raise ConnectionError("Error: a connection was not initiated, use 'connect' first.")
        return self._sock.recv(max_bytes)


class _CommandsMetaClass(type):
    """
    The actual commands class.
    _CommandsMetaClass is used as a meta class. so Commands can use its __getattr__ without
    the need to create an instance of it.
    """
    commands_dict = {"clearerror": None,
                     "currentsong": None,
                     "idle": ("subsystems",),
                     "status": None,
                     "stats": None,
                     "consume": ("state",),
                     "crossfade": ("seconds",),
                     "mixrampdb": ("decibels",),
                     "mixrampdelay": ("seconds",),
                     "random": ("state",),
                     "repeat": ("state",),
                     "setvol": ("vol",),
                     "single": ("state",),
                     "replay_gain_mode": ("mode",),
                     "replay_gain_status": None,
                     "volume": ("change",),  # Deprecated
                     "next": None,
                     "pause": ("pause",),  # Using without the argument is deprecated
                     "play": ("songpos",),
                     "playid": ("songid",),
                     "previous": None,
                     "seek": ("songpos", "time"),
                     "seekid": ("songid", "time"),
                     "seekcur": ("time",),
                     "stop": None,
                     "add": ("uri",),
                     "addid": ("uri", "position"),
                     "clear": None,
                     "delete": ("pos", "start_end"),
                     "deleteid": ("songid",),
                     "move": ("from", "start_end", "to"),
                     "moveid": ("from", "to"),
                     "playlist": None,  # Use playlistinfo instead
                     "playlistfind": ("tag", "needle"),
                     "playlistid": ("songid",),
                     "playlistinfo": ("songpos", "start_end"),
                     "playlistsearch": ("tag", "needle"),
                     "plchanges": ("version",),
                     "plchangeposid": ("version",),
                     "prio": ("priority", "start_end"),
                     "prioid": ("priority", "id"),
                     "rangeid": ("id", "start_end"),
                     "shuffle": ("start_end",),
                     "swap": ("song1", "song2",),
                     "swapid": ("song1", "song2",),
                     "addtagid": ("songid", "tag", "value"),
                     "cleartagid": ("songid", "tag"),
                     "listplaylist": ("name",),
                     "listplaylistinfo": ("name",),
                     "listplaylists": None,
                     "load": ("name", "start_end"),
                     "playlistadd": ("name", "uri"),
                     "playlistclear": ("name",),
                     "playlistdelete": ("name", "songpos"),
                     "playlistmove": ("name", "songid", "songpos"),
                     "rename": ("name", "new_name"),
                     "rm": ("name",),
                     "save": ("name",),
                     "count": ("tag", "needle", "group", "grouptype"),
                     "find": ("type", "what"),
                     "findadd": ("type", "what"),
                     "list": ("type", "filtertype", "filterwhat", "group", "grouptype"),
                     "listall": ("uri",),
                     "listallinfo": ("uri",),
                     "listfiles": ("uri",),
                     "lsinfo": ("uri",),
                     "readcomments": ("uri",),
                     "search": ("type", "what"),
                     "searchadd": ("type", "what"),
                     "searcgaddpl": ("name", "type", "what"),
                     "update": ("uri",),
                     "rescan": ("uri",),
                     "mount": ("path", "uri"),
                     "unmount": ("path",),
                     "listmounts": None,
                     "listneighbors": None,
                     "sticker": ("cmd", "type", "uri", "name", "value"),  # Multiple commands in one
                     "close": None,
                     "kill": None,
                     "password": ("password",),
                     "ping": None,
                     "disableoutput": ("id",),
                     "enableoutput": ("id",),
                     "toggleoutput": ("id",),
                     "outputs": None,
                     "config": None,
                     "commands": None,
                     "notcommands": None,
                     "tagtypes": None,
                     "urlhandlers": None,
                     "decoders": None,
                     "subscribe": ("name",),
                     "unsubscribe": ("name",),
                     "channels": None,
                     "readmessages": None,
                     "sendmessages": ("channel", "text")}

    def __getattr__(self, item):
        """
        Makes the class generate dynamically the functions

        :param item: command requested (as above)
        :type item: Str
        :return: the command
        :rtype: Function
        """
        if item not in _CommandsMetaClass.commands_dict:
            raise MPDCommandNotExists("no such command: '{}'".format(item))

        f = lambda *args: "{} {}\n".format(item, ' '.join(_CommandsMetaClass._quote_arguments(args)))
        f.__doc__ = "Command's Arguments: {}".format(_CommandsMetaClass.commands_dict[item])
        f.__name__ = item
        return f

    @staticmethod
    def _quote_arguments(args):
        """
        Quotes the items in args that contain spaces

        :param args: a list of strings
        :type args: list(str)
        """
        return map(lambda x: '"{}"'.format(x) if ' ' in x else '{}'.format(x), args)


class Commands(object):
    """
    Stores the available commands in MPD protocol.
    commands_dict stores the available commands. Their arguments tuple is used for convenience,
    and can be found at each command __doc__.
    """
    __metaclass__ = _CommandsMetaClass


class Parser(object):
    """
    Used to parse a mpd response and convert it into a python object
    """

    LINE_DELIM = '\n'
    FIELD_DELIM = ': '
    OK_MSG = 'OK'
    NOT_OK_MSG = 'ACK'

    @staticmethod
    def parse(string):
        """
        Parses the string and try to create a python object of it (like json)
        :param string: The string to parse
        :type string: string
        :return: a pythonic object of the result
        :rtype: bool or list
        """
        if string.strip() == Parser.OK_MSG or string.startswith(Parser.NOT_OK_MSG):
            return Parser._handle_ok_ack(string)
        results = Parser._handle_dict(string)
        results.extend(Parser._handle_else(string))
        return results

    @staticmethod
    def _handle_ok_ack(string):
        """
        returns True or False.
        True is when the response in OK, and indicates that a valid commands was sent to mpd.
        False is otherwise (in most cases- invalid command).
        """
        if string.strip() == Parser.OK_MSG:
            return True
        return False

    @staticmethod
    def _handle_dict(string):
        """
        Makes a dict out of the string received
        """
        dict_lines = [line.split(Parser.FIELD_DELIM) for line in string.split(Parser.LINE_DELIM)
                      if Parser.FIELD_DELIM in line]
        cur_dict = 0
        results = [{}]
        for line in dict_lines:
            if line[0] in results[cur_dict]:
                results.append({})
                cur_dict += 1
            results[cur_dict][line[0]] = line[1]
        return results

    @staticmethod
    def _handle_else(string):
        """
        Handle everything that is not anything else :)
        """
        return [line for line in string.split(Parser.LINE_DELIM) if Parser.FIELD_DELIM not in line and line != ''
                and line != Parser.OK_MSG]


class OMMPCException(Exception):
    pass


class MPDCommandError(OMMPCException):
    pass


class MPDCommandNotExists(OMMPCException):
    pass


class ConnectionError(OMMPCException):
    pass
