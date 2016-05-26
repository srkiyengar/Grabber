__author__ = 'srkiyengar'

import socket
import logging
import struct
import datetime


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

    def receive_data(self,how_many):

        received_data = []
        bytes_recd = 0
        while bytes_recd < how_many:
            chunk = self.sock.recv((how_many - bytes_recd), 2048)
            if chunk == '':
                raise RuntimeError("socket connection broken")
            received_data.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        return ''.join(received_data)


class command_labview:

        def __init__(self, host, port=5000):

            self.my_connection = make_connection()
            self.my_connection.connect(host,port)
            self.datafile = ""

        def exchange_time(self, time_str):

            #my_logger.info("Starting Time: {}".format(datetime.datetime.now()))
            l = len(time_str)
            format_str = "BB"+str(l)+"s"
            send_str = struct.pack(format_str,6,l,time_str)
            self.my_connection.send_data(send_str)
            #my_logger.info("After Sending the Time is: {}".format(datetime.datetime.now()))
            response_header = self.my_connection.receive_data(2)
            #my_logger.info("Response header received at time: {}".format(datetime.datetime.now()))
            c = ord(response_header[1])
            response_str = self.my_connection.receive_data(c)
            #my_logger.info("Response string received at time: {}".format(datetime.datetime.now()))
            return response_str

        def send_unimplemented_command(self):
            some_string = "nothing"
            l = len(some_string)
            format_str = "BB"+str(l)+"s"
            end_str = struct.pack(format_str,4,l,some_string)
            self.my_connection.send_data(end_str)

        def start_collecting(self,filename):
            self.datafile = filename
            l = len(filename)
            format_str = "BB"+str(l)+"s"
            start_str = struct.pack(format_str,7,l,filename)
            self.my_connection.send_data(start_str)
            my_logger.info("Sent Command to NDI to Start Collecting for {}".format(filename))

        def stop_collecting(self):
            if self.datafile:
                l = len(self.datafile)
                format_str = "BB"+str(l)+"s"
                stop_str = struct.pack(format_str,5,l,self.datafile)
                self.my_connection.send_data(stop_str)
                my_logger.info("Sent Command to NDI to Stop Collecting for {}".format(self.datafile))

        def stop__labview_recording(self):
            filename = "dummy"
            l = len(filename)
            format_str = "BB"+str(l)+"s"
            end_str = struct.pack(format_str,6,l,filename)
            self.my_connection.send_data(end_str)
            self.my_connection.send_data(end_str)       #the labivew seems to requires two for while loop shutdonw - needs debugging

        def destroy(self):
            self.my_connection.end_socket()





