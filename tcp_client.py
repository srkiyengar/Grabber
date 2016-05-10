__author__ = 'srkiyengar'

import socket
import logging
import struct

LOG_LEVEL = logging.DEBUG

# Set up a logger with output level set to debug; Add the handler to the logger
my_logger = logging.getLogger("My_Logger")


class make_connection:

    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(10)
        else:
            self.sock = sock

    def connect(self, host, port):
        try:
            self.sock.connect((host,port))
        except socket.timeout:
            my_logger.info("Socket time out error")

    def end_socket(self):
        #self.sock.shutdown(self.sock)
        self.sock.close()

    def send_data(self, msg):

        message_len = len(msg)
        total = 0
        while total < message_len:
            sent = self.sock.send(msg[total:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            total = total + sent


class command_labview:

        def __init__(self, host, port=5000):
            self.my_connection = make_connection()
            self.my_connection.connect(host,port)
            self.datafile = ""

        def start_collecting(self,filename):
            self.datafile = filename
            l = len(filename)
            format_str = "BB"+str(l)+"s"
            start_str = struct.pack(format_str,7,l,filename)
            self.my_connection.send_data(start_str)

        def stop_collecting(self):
            if self.datafile:
                l = len(self.datafile)
                format_str = "BB"+str(l)+"s"
                stop_str = struct.pack(format_str,5,l,self.datafile)
                self.my_connection.send_data(stop_str)

        def stop__labview_recording(self):
            filename = "dummy"
            l = len(filename)
            format_str = "BB"+str(l)+"s"
            end_str = struct.pack(format_str,6,l,filename)
            self.my_connection.send_data(end_str)
            self.my_connection.send_data(end_str)       #Yest the labivew requires two - needs debugging

        def destroy(self):
            self.my_connection.end_socket()





