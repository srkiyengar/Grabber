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
        my_logger.info("Dataset creating begun at " + time.strftime("%d-%b-%Y %H:%M:%S", time.localtime()))
        some_random_number = random.randrange(MIN_RANDOM_NUMBER_DATASET,MAX_RANDOM_NUMBER_DATASET)
        self.data_batch = some_random_number # will not be changed
        self.counter = 0
        self.empty = 1

    def append(self,ycb_object_dataset):
        self.data.append(ycb_object_dataset)
        self.empty = 0

    def get_object_id(self):
        c = self.counter
        object_id = STARTING__OBJECT_NUMBER+c
        self.counter = c + 1
        return object_id



class ycb_object_dataset:

    def __init__(self,my_dataset):
        self.ycb_object =[]
        t = time.localtime()
        creation_time = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())
        self.object_id = my_dataset.get_object_id()
        self.batch = my_dataset.data_batch
        my_logger.info("{} - Inserted-Batch: {} object: {}".format(creation_time,
                                                                    self.batch,self.object_id))
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
        return id;

class data:

    def __init__(self, my_ycb_object_dataset):
        self.filenumber = my_ycb_object_dataset.get_file_id()
        self.batch = my_ycb_object_dataset.get_batch()
        self.ycb_object = my_ycb_object_dataset.get_ycb_object()
        self.filename = str(self.batch)+"-"+str(self.ycb_object)+"-"+str(self.filenumber)
        my_ycb_object_dataset.append(self)

    def get_data_filename(self):
        return self.filename


