__author__ = 'srkiyengar'


import pygame
import pygame.camera
import os
import logging

LOG_LEVEL = logging.DEBUG



# Set up a logger with output level set to debug; Add the handler to the logger
my_logger = logging.getLogger("My_Logger")


class webcam:
    def __init__( self, cam_identifier, focus_type, focus_value):

        if focus_type != 0 or focus_type != 1:
            focus_type = 0
        if cam_identifier !=0 and cam_identifier!=1:
            cam_identifier = 1
        dev = "/dev/video"+str(cam_identifier)
        part_command = "v4l2-ctl -d " + dev
        input_string = part_command +" --set-ctrl focus_auto="+str(focus_type)
        my_logger.info("Setting to manual-focus: {}".format(input_string))
        if os.system(input_string) == 0:
            if focus_type == 0:
                input_string = part_command +" --set-ctrl focus_absolute="+str(1)
                my_logger.info("Focus value: {}".format(input_string))
            else:
                pass
            if os.system(input_string) == 0:
                pygame.camera.init()
                self.camera = pygame.camera.Camera(dev,(1920,1080))
                self.camera.start()
                return
            else:
                return None
        else:
            return None




    def capture_and_save_frame(self,filename):

        # input_string = "v4l2-ctl -d /dev/video1 --set-fmt-video=width=1920,height=1080,pixelformat=1"
        # if (os.system(input_string) == 0):
        cam = self.camera
        img = cam.get_image()
        pygame.image.save(img,filename+".png")


    def close_video(self):
        cam = self.camera
        cam.stop() # Close window
