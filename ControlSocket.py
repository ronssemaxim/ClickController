"""
ControlSocket.py. Used to connect to a Click Control Socket (see read.cs.ucla.edu/click/elements/controlsocket)

Ronsse Maxim <maxim.ronsse@ugent.be | ronsse.maxim@gmail.com>
"""
import socket


class ClickControlSocketClient:
    BUFFER_SIZE = 1024
    TERMINATOR = "yU6Ap5uq8X*h@sTU68ekURecrakeThej"  # a random terminator, should never occur in the data

    def __init__(self, ip, port):
        """
        Initialize object and connect to the socket
        :param ip: Remote IP
        :param port: Remtoe port
        """
        self.ip = ip
        self.port = port
        self.conn = socket.socket()

        self.conn.connect((ip, port))

    def send(self, data):
        """
        Send plain text to the control socket.
        :param data: the data, in plain text, to send
        :return:
        """
        send = data + "\n"
        print(send)
        self.conn.send(send.encode())
        return self.conn.recv(self.BUFFER_SIZE).decode()

    def get_config(self):
        """
        Get complete Click configuration
        :return: string
        """
        return self.send("read config")

    def set_config(self, configLines):
        """
        Set the Click configuration (hotswap using hotconfig global handler)
        :param configLines:
        :return:
        """
        return self.send("writeuntil hotconfig " + self.TERMINATOR + "\n" + configLines + "\n" + self.TERMINATOR)

    def get_flat_config(self):
        """
        Get config with the element numbers.
        :return: string. Eg FromDevice@1->Discard@2;
        """
        return self.send("read config")

    def __exit__(self, exc_type, exc_value, traceback):
        # Destructor
        if self.conn:
            self.conn.close()


'''
Test code:
 click = ClickControlSocketClient("127.0.0.1", 1234)
print(click.set_config("""ICMPPingSource(192.168.123.10, 192.168.123.123, INTERVAL 2)
	-> rt::RadixIPsecLookup(192.168.123.11/32 0,
                        192.168.123.123/32 192.168.123.12 1 234 ABCDEFFF001DEFD2 ABCDEFFF001DEFD2 1 64,
                        192.168.123.12/32 2);

rt[0] -> IPPrint(firstMatch) -> Discard;
rt[1] -> IPPrint(secondMatch) -> Discard
rt[2] -> IPPrint(thirdMatch) -> Discard"""))
'''
