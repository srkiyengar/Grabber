__author__ = 'srkiyengar'

import random
import time
import logging


LOG_LEVEL = logging.DEBUG

MIN_RANDOM_NUMBER_DATASET = 10000000
MAX_RANDOM_NUMBER_DATASET = 99999999


STARTING__OBJECT_NUMBER = 0
STARTING_FILE_NUMBER =1000



# Set up a logger with output level set to debug; Add the handler to the logger
my_logger = logging.getLogger("My_Logger")


class dataset:

    def __init__(self):
        self.data = []
        self.timestamp = time.localtime()
        my_logger.info("******Dataset creation begun at " + time.strftime("%d-%b-%Y %H:%M:%S", time.localtime()) + "***")
        some_random_number = random.randrange(MIN_RANDOM_NUMBER_DATASET,MAX_RANDOM_NUMBER_DATASET)
        self.data_batch = some_random_number # will not be changed
        self.counter = 0
        self.empty = 1
        self.clock_difference = None

    def append(self,ycb_object_dataset):
        self.data.append(ycb_object_dataset)
        self.empty = 0

    def get_object_id(self):
        c = self.counter
        object_id = STARTING__OBJECT_NUMBER+c
        self.counter = c + 1
        return object_id

    def set_clock_difference(self,clock_difference):
        # positive clock difference means that the Labview data is ahead of Grabber time (microseconds)
        self.clock_difference = clock_difference


class ycb_object_dataset:

    def __init__(self,my_dataset):
        self.ycb_object =[]
        t = time.localtime()
        creation_time = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())
        self.object_id = my_dataset.get_object_id()
        self.batch = my_dataset.data_batch
        self.clock_diff = my_dataset.clock_difference
        my_logger.info("*******Batch: {} At {} Created object: {} ************".format(self.batch, creation_time,
                                                                    self.object_id))
        self.file_counter = 0
        my_dataset.append(self)

    def append(self,onedata):
        self.ycb_object.append(onedata)

    def get_batch(self):
        return self.batch

    def get_ycb_object(self):
        return self.object_id

    def get_file_id(self):
        d = self.file_counter
        id = STARTING_FILE_NUMBER+d
        self.file_counter = d + 1
        return id
    def get_clock_difference(self):
        return self.clock_diff

class data:

    def __init__(self, my_ycb_object_dataset):
        self.filenumber = my_ycb_object_dataset.get_file_id()
        self.batch = my_ycb_object_dataset.get_batch()
        self.ycb_object = my_ycb_object_dataset.get_ycb_object()
        self.filename = str(self.batch)+"-"+str(self.ycb_object)+"-"+str(self.filenumber)
        self.clock_difference = my_ycb_object_dataset.get_clock_difference()

        try:
            data_file_fp = open(self.filename,"w")
        except IOError:
            my_logger.info("Failure to open File {}:".format(self.filename))
            raise IOError ("Unable to open file for Grabber Finger position recording")
        self.file_pointer = data_file_fp

        my_ycb_object_dataset.append(self)

    def get_data_filename(self):
        return self.filename


    def close_data_file(self):
        self.file_pointer.close()


    def write_data_file(self,write_str):
        self.file_pointer.write(write_str)


class data_elements:

    def __init__(self):

        self.loop_ts = None
        self.joystick_value_ts = None
        self.joystick_0 = None
        self.joystick_1 = None
        self.goal_position = [0,0,0,0,0]  # ignore index 0 1 to 4 correspond to servo 1 to 4
        self.gp_ts = None
        self.current_position = [0,0,0,0,0] # ignore index 0 1 to 4 correspond to servo 1 to 4 this is be poor as \
                                            # servo is moving
        self.cp_ts = None

    def set_time(self, loop_ts=None, joystick_value_ts = None, gp_ts = None, cp_ts = None):

        if loop_ts:
            self.loop_ts = loop_ts
        if joystick_value_ts:
            self.joystick_value_ts = joystick_value_ts
        if gp_ts:
            self.gp_ts = gp_ts
        if cp_ts:
            self.cp_ts = cp_ts

    def set_position_gp(self, gp):
        self.goal_position = gp

    def get_position_gp(self):
        return self.goal_position

    def set_position_cp(self,cp):
        self.current_position = cp

    def get_position_gp(self):
        return self.current_position

    def write_to_file(self,my_data):
        write_str = "{},{},{},{},{},{},{},{}\n".format(self.loop_ts,self.joystick_value_ts,self.joystick_0,self.joystick_1,\
                        self.gp_ts,self.goal_position,self.cp_ts,self.current_position)
        my_data.write_data_file(write_str)

