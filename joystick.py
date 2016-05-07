__author__ = 'srkiyengar'
# Significant joystick code or the basis of it comes from pygame.joystick sample code
import pygame


# Before invoking this class pygame.init() needs to be called
# calling methods would require an event call like get or pump
# The looping has to be in the external invocation
# End should have pygame quit

class ExtremeProJoystick():
    def __init__( self):
        # Initialize the joysticks
        pygame.joystick.init()
        self.joystick_count = pygame.joystick.get_count()
        if self.joystick_count == 0:
            raise RuntimeError('No Joystick not found\n')
        else:
            My_joystick = pygame.joystick.Joystick(0)
            name = My_joystick.get_name()
            if ("Logitech Extreme 3D" in name):
                self.name = name
                My_joystick.init()
                self.axes = My_joystick.get_numaxes()
                self.buttons = My_joystick.get_numbuttons()
                self.hats = My_joystick.get_numhats()
                self.joystick= My_joystick
            else:
                raise RuntimeError('Logitech Extreme #D Joystick not found\n')

