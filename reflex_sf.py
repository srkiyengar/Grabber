__author__ = 'srkiyengar'



import dynamixel
import pygame
import joystick
from datetime import datetime
import logging
import logging.handlers
import create_dataset as cd
import image_capture as ic
import tcp_client as tc



JOY_DEADZONE_A0 = 0.2
JOY_DEADZONE_A1 = 0.1

SCAN_RATE = 100           #1 second divided by scan rate is t he joystick scanning
POS_ERROR = 20

MOVE_TICKS = 250
CALIBRATION_TICKS = 50


MAX_FINGER_MOVEMENT = 2300
MAX_PRESHAPE_MOVEMENT = 1550

MAX_SPEED = 200 # A max speed of 1023 is allowed

REPORT_PALM_POSITIONS = 1  #To report finger positions using A3 movement of joystick

#logger
LOG_LEVEL = logging.DEBUG
LOG_FILENAME = 'Grabber' + datetime.now().strftime('%Y-%m-%d---%H:%M:%S')


# Since Fingers start from 1 to 4, list and tuples will have index 0 left unused.

class reflex_sf():
    '''The class manages the calibration and movement of the fingers for pinch and grasp
    '''
    def __init__(self, usb_channel = '/dev/ttyUSB0', baudrate = 57600):
        dyn = dynamixel.USB2Dynamixel_Device(usb_channel, baudrate)
        l_limits = [0,13920,16740,15600, 14980]
        u_limits = [0,0,0,0,0]

        try:
            fp = open("calibration","r")
        except IOError:
            raise IOError("Unable to open calibration file")

        cal_str = fp.readline()
        j = 0
        for i in cal_str.split(','):
            l_limits[j] = int(i)
            j = j + 1
        fp.close()
        my_logger.info("Rest Positions F1-{} F2-{} F3-{} F4 {}".format
                       (l_limits[1],l_limits[2],l_limits[3],l_limits[4]))
        self.finger = []
        self.finger.append(0) # finger starts with 1. Inserting 0 at the first list position

        for i in range(1,5,1):
            try:
                # using the USB2Dynamixel object try to send commands to each and receive information
                j= dynamixel.Robotis_Servo(dyn, i,"MX" )
            except:
                raise RuntimeError('Connection to Servo failure for servo number', i,'\n')
            temp = j.read_temperature()
            resol = j.read_resolution_divider()
            current_pos = j.read_current_position()
            goal_pos = j.get_goal_position()
            offset = j.read_offset()
            speed = MAX_SPEED
            j.set_speed(speed)
            if i==1:
                joint_state = 1
                u_limits[i] = l_limits[i] + MAX_FINGER_MOVEMENT
            elif i==2:
                joint_state = -1
                u_limits[i] = l_limits[i] - MAX_FINGER_MOVEMENT
            elif i==3:
                joint_state = 1
                u_limits[i] = l_limits[i] + MAX_FINGER_MOVEMENT
            elif i==4:
                joint_state = -1
                u_limits[i] = l_limits[i] - MAX_PRESHAPE_MOVEMENT

            max_torque = j.read_max_torque()
            set_torque = j.read_set_torque()
            finger_parameters = {"servo":j, "temperature": temp, "resolution_divider": resol, "initial_position": current_pos,
                                 "goal_position":goal_pos,"multi_turn_offset":offset, "moving_speed":speed, "direction": 1,
                                 "lower_limit":l_limits[i],"upper_limit":u_limits[i],"rotation":joint_state,
                                 "max_torque":max_torque, "set_torque":set_torque, "CP":current_pos}
            self.finger.append(finger_parameters)

    def get_palm_rest_position(self):   #Returns a list of current lower limit
        rest_limits = [0,0,0,0,0]
        for i in range(1,5,1):
            rest_limits[i] = self.finger[i]["lower_limit"]
        return rest_limits

    def set_palm_rest_position(self,set_limits):
        for i in range(1,5,1):
            self.finger[i]["lower_limit"] = set_limits[i]
            if i==1:
                self.finger[i]["upper_limit"] = set_limits[i] + MAX_FINGER_MOVEMENT
            elif i==2:
                self.finger[i]["upper_limit"] = set_limits[i] - MAX_FINGER_MOVEMENT
            elif i==3:
                self.finger[i]["upper_limit"] = set_limits[i] + MAX_FINGER_MOVEMENT
            elif i==4:
                self.finger[i]["upper_limit"] = set_limits[i] - MAX_PRESHAPE_MOVEMENT
            x = self.finger[i]["lower_limit"]
            y = self.finger[i]["upper_limit"]
            my_logger.debug('Finger {} Lower Limit {} -- Upper Limit {}'.format(i,x,y))
        return 1


    def get_palm_current_position(self): #Returns a list of current position
        current_position = [0,0,0,0,0]
        for i in range(1,5,1):
            current_position[i] = self.finger[i]["CP"]
        return current_position

    def read_servo_current_location(self):
        current_location = [0,0,0,0,0]
        for i in range(1,5,1):
            current_location[i] = self.finger_current_position(i)
        return current_location

    def is_finger_within_limit(self, id, new_position):
        ll = self.finger[id]["lower_limit"]
        ul = self.finger[id]["upper_limit"]
        rotation_mode = self.finger[id]["rotation"]
        if rotation_mode == 1:
            if ul >= new_position >= ll:
                return new_position
            else:
                if new_position > ul:
                    new_position = ul
                elif new_position < ll:
                    new_position = ll
                my_logger.debug('Finger {} new position changed to {}'.format(id,new_position))
                return new_position
        elif rotation_mode == -1:
           if ll>=new_position >= ul:
               return new_position
           else:
               if new_position > ll:
                    new_position = ll
               elif new_position < ul:
                    new_position = ul
               my_logger.debug('Finger {} new position changed to {}'.format(id,new_position))
               return new_position
        else:
            my_logger.debug("Finger{} joint rotation mode: {} unknown",format(rotation_mode))
            return 0

    def finger_current_position(self,id):
        while (self.finger[id]["servo"].is_moving()):
            pass
        p = self.finger[id]["servo"].read_current_position()
        #my_logger.debug('Finger{} - Current Position {}'.format(id,p))
        return p

    def finger_load(self,id):
        load, rotation = self.finger[id]["servo"].read_and_convert_raw_load()
        return load, rotation

    def move_finger_delta(self, id, move_direction,increment): # direction +1 = finger closing; -1 = finger opening
        p = self.finger[id]["CP"]
        #p = self.finger[id]["servo"].read_current_position()
        #my_logger.debug('Finger {} position from Servo {}'.format(id,p))
        q = self.finger[id]["rotation"]
        q *= move_direction
        new_position = p + q*increment
        move_to = self.is_finger_within_limit(id,new_position)
        #my_logger.debug('After - Finger {} - CP {}'.format(id,move_to))
        if move_to > 0:
            my_logger.info("Finger {}: MoveFrom: {} To: {} - LimitedTo: {}".format(id,p,new_position,move_to))
            #my_logger.info('Finger {} - Moving From Position {} to Position {}'.format(id,p,move_to))
            self.finger[id]["servo"].set_goal_position(move_to) # return data to make the program wait
            self.finger[id]["CP"] = move_to     # new_position when out of bounds will be modified. Therefore
            return move_to
        else:
            my_logger.info\
                ('Outside Limit Finger{} - Denied: Move From Position {} to Position {}'.format(id,p,new_position))
            return 0

    def grip_fingers(self, move_by, grip, recording=None, file_pointer=None):
        if grip == 1:
            my_logger.info('Tighten by {} '.format(move_by))
        elif grip == -1:
            my_logger.info('Loosen by {} '.format(move_by))

        for i in range(1,4,1):
            self.move_finger_delta(i,grip,move_by)

        #updating CP to match current position
        #for i in range(1,4,1):
            #p = self.finger[i]["CP"]
            #q = self.finger[i]["servo"].read_current_position()
            #q = self.finger_current_position(i)
            #my_logger.debug('Finger {} should at {} and it is at {}'.format(i,p,q))
            #self.finger[i]["CP"] = q

        if recording is not None:
            F = self.get_palm_current_position()
            file_pointer.write("F1-"+ str(F[1])+",F2-"+str(F[2])+",F3-"+ str(F[3])+",F4-"+str(F[2])+"\n")

    def space_finger1_and_finger2(self, move_by, grip,recording=None, file_pointer=None):
        if grip == 1:
            my_logger.info('Spread finger 1 and 3 by {}'.format(move_by))
        elif grip == -1:
            my_logger.info('Bring finger 1 and 3 closer by {}'.format(move_by))
        self.move_finger_delta(4,grip,move_by)
        if recording is not None:
            F = self.get_palm_current_position()
            file_pointer.write("F1-"+ str(F[1])+",F2-"+str(F[2])+",F3-"+ str(F[3])+",F4-"+str(F[2])+"\n")

    def manual_move_finger_to_position(self,servo_id, move_direction):
        increment = CALIBRATION_TICKS
        self.manual_move_finger_delta(servo_id,move_direction,increment)
        p = self.finger_current_position(sid)
        self.finger[servo_id]["CP"] = p

    def manual_move_finger_delta(self, id, move_direction,increment): # direction +1 = finger closing; -1 = finger opening
        #p = self.finger[id]["CP"]
        p = self.finger_current_position(id)
        my_logger.debug('Finger {} MoveFrom: {}'.format(id,p))
        q = self.finger[id]["rotation"]
        q *= move_direction
        new_position = p + q*increment
        #move_to = self.is_finger_within_limit(id,new_position)
        move_to = new_position
        my_logger.debug('Finger {} MoveTo: {}'.format(id,move_to))
        if move_to > 0:
            self.finger[id]["servo"].set_goal_position(move_to) # return data to make the program wait
            #self.finger[id]["CP"] = move_to     # new_position when out of bounds will be modified. Therefore
        return move_to

    def move_to_rest_position(self):
        current_position = self.read_servo_current_location()
        for i in range(1,5,1):
            rest_position = self.finger[i]["lower_limit"]
            my_logger.info("Moving  Servo {} From {} to Rest position {}".format(i, current_position[i],rest_position))
            self.finger[i]["servo"].set_goal_position(rest_position)
            self.finger[i]["CP"] = rest_position
        return

    def get_rest_position(self):
        F = []
        F.append(0)
        for i in range(1,5,1):
            rest_position = self.finger[i]["lower_limit"]
            F.append(rest_position)
        return F
    def get_max_position(self):
        F=[]
        F.append(0)
        for i in range(1,5,1):
            max_position = self.finger[i]["upper_limit"]
            F.append(max_position)
        return F

# Define some colors
BLACK    = (   0,   0,   0)
WHITE    = ( 255, 255, 255)

# This is a simple class that will help us print to the screen
# It has nothing to do with the joysticks, just outputing the
# information.
class TextPrint:
    def __init__(self):
        self.reset()
        self.font = pygame.font.Font(None, 20)

    def Screenprint(self, screen, textString):
        textBitmap = self.font.render(textString, True, BLACK)
        screen.blit(textBitmap, [self.x, self.y])
        self.y += self.line_height

    def reset(self):
        self.x = 10
        self.y = 10
        self.line_height = 15

    def indent(self):
        self.x += 10

    def unindent(self):
        self.x -= 10

    def Yspace(self):
        self.y += 10


if __name__ == '__main__':



    # Set up a logger with output level set to debug; Add the handler to the logger
    my_logger = logging.getLogger("My_Logger")
    my_logger.setLevel(LOG_LEVEL)
    handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=2000000, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    my_logger.addHandler(handler)
    # end of logfile preparation Log levels are debug, info, warn, error, critical


    palm = reflex_sf() # Reflex object ready

    my_logger.info('Reflex_SF object created')


    for i in range(1,5,1):
        lowest_position = palm.finger[i]["lower_limit"]
        highest_position = palm.finger[i]["upper_limit"]
        init_position = palm.finger[i]["initial_position"]
        max_torque_setting = palm.finger[i]["max_torque"]
        allowable_torque = palm.finger[i]["set_torque"]

        my_logger.info('--- Finger {}:'.format(i))
        my_logger.info('       Max Torque --- {}'.format(max_torque_setting))
        my_logger.info('       Allowable Torque --- {}'.format(allowable_torque))
        my_logger.info('       Lower Limit Position --- {}'.format(lowest_position))
        my_logger.info('       Upper Limit Position --- {}'.format(highest_position))
        my_logger.info('       Initial Position {}'.format(init_position))

        calibrate = 0

        if (i == 1 or i == 3):
            a = lowest_position - POS_ERROR
            b= highest_position + POS_ERROR
            if a >= init_position or init_position >= b:
                my_logger.info('Servo {} Initial Position {} not between Lower Limit {} and Upper Limit {}'\
                               .format(i,init_position,lowest_position,highest_position))
                print('Servo {} Initial Position {} not between Lower Limit {} and Upper Limit {}'.format(\
                    i,init_position,lowest_position,highest_position))
                calibrate = 1
        elif (i == 2):
            a = lowest_position + POS_ERROR
            b = highest_position - POS_ERROR
            if a <= init_position or init_position <= b:
                my_logger.info('Servo {} Initial Position {} not between Lower Limit {} and Upper Limit {}'\
                               .format(i,init_position,lowest_position,highest_position))
                print('Servo {} Initial Position {} not between Lower Limit {} and Upper Limit {}'.format(\
                    i,init_position,lowest_position,highest_position))
                calibrate = 1

    pygame.init()

    # Set the width and height of the screen [width,height]
    size = [500, 700]
    screen = pygame.display.set_mode(size)

    pygame.display.set_caption("Reflex_SF JoyStick Movements")

    #Setup Webcam for manual focus with focus setting to 1 (It can be set to 1 to 27)
    my_cam = ic.webcam(1,0,1) #Camera =1, Autofocus = 0, focus setting = 1

    #creating the root for list that will contain information on each object data collection
    my_dataset = cd.dataset()

    # a flag to print and stop printing finger positions to data file
    set_record = 0

    #setup labview connection
    my_command = tc.command_labview('192.168.10.2', 5000)

    # my_command.send_unimplemented_command()     # does nothing

    for m in range(1,6,1):
        my_logger.info("Attempt # {}".format(m))
        before_time_str = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        response_str = my_command.exchange_time(before_time_str)
        after_time_str = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        my_logger.info("Before Laptop Time: {}".format(before_time_str))
        my_logger.info("Desktop Response: {}".format(response_str))
        my_logger.info("After Laptop Time: {}".format(after_time_str))



    # Used to manage how fast the screen updates
    clock = pygame.time.Clock()

    # Get ready to print
    textPrint = TextPrint()

    j_device = joystick.ExtremeProJoystick()
    # Get count of joystick
    Buttons = []
    Num_Buttons = j_device.buttons

    min_val = [-JOY_DEADZONE_A0,-JOY_DEADZONE_A1,0,0]
    max_val = [JOY_DEADZONE_A0,JOY_DEADZONE_A1,0,0]

    Num_Axes = j_device.axes
    Num_Hats =j_device.hats

    A3_palm_position_reporting = REPORT_PALM_POSITIONS #while using Joystick A3 = 1, we want only one print out
    old_datafile = ""                         #to close previous data file

    for i in range (Num_Buttons):
        Buttons.append(0)

    Axes = []   #mainly for the screen display
    for i in range (Num_Axes):
        Axes.append(0.00)

    move_goal = [0,0,0,0]
    Hat = (0,0)
    joy_move = [0,0,0,0]
    direction = [0,0,0,0]

    #Loop until the user clicks the close button.
    done = False

    # -------- Main Program Loop -----------
    while done==False:
        screen.fill(WHITE)
        textPrint.reset()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            elif event.type == pygame.JOYAXISMOTION:
                pass
            elif event.type == pygame.JOYBUTTONDOWN:
                i = event.dict['button']    # button number
                Buttons[i] = 1
                my_logger.debug("Button {} pressed".format(i))
                if Buttons[11] == 1:
                    sid = 3
                    grip = 1
                    palm.manual_move_finger_to_position(sid,grip)
                elif Buttons[10] == 1:
                    sid = 3
                    grip = -1
                    palm.manual_move_finger_to_position(sid,grip)
                elif Buttons[9] == 1:
                    sid = 2
                    grip = 1
                    palm.manual_move_finger_to_position(sid,grip)
                elif Buttons[8] == 1:
                    sid = 2
                    grip = -1
                    palm.manual_move_finger_to_position(sid,grip)
                elif Buttons[7] == 1:
                    sid = 1
                    grip = 1
                    palm.manual_move_finger_to_position(sid,grip)
                elif Buttons[6] == 1:
                    sid = 1
                    grip = -1
                    palm.manual_move_finger_to_position(sid,grip)
                elif Buttons[3] == 1:
                    sid = 4
                    grip = 1
                    palm.manual_move_finger_to_position(sid,grip)
                elif Buttons[2] == 1:
                    sid = 4
                    grip = -1
                    palm.manual_move_finger_to_position(sid,grip)


                elif Buttons[1] == 1:
                    palm.move_to_rest_position()
                    fingers = palm.get_palm_current_position()
                    my_logger.info("Finger Rest Positions F1-{} F2-{} F3-{} F4-{}".format
                    (fingers[1],fingers[2],fingers[3],fingers[4]))

                    fingers = palm.read_servo_current_location()
                    my_logger.info("Servo Rest Positions F1-{} F2-{} F3-{} F4-{}".format
                    (fingers[1],fingers[2],fingers[3],fingers[4]))

                elif Buttons[0] == 1:
                    fingers = palm.get_palm_current_position()
                    my_logger.info("Current Finger Positions F1-{} F2-{} F3-{} F4-{}".format
                    (fingers[1],fingers[2],fingers[3],fingers[4]))
                elif Buttons[4] and Buttons[5]:
                    my_logger.info("New Finger positions - calibration")
                    try:
                        fp = open("calibration","w")
                    except IOError:
                        raise IOError ("Unable to open calibration file")

                    new_limits = palm.get_palm_current_position()
                    palm.set_palm_rest_position(new_limits)
                    my_logger.info("Calibration - New Rest Positions F1-{} F2-{} F3-{} F4 {}".format
                    (new_limits[1],new_limits[2],new_limits[3],new_limits[4]))
                    s = str(new_limits)
                    nes = s[1:]     # Remove [
                    ges = nes[:-1]  # Remove ]
                    fp.write(ges)   # write the remaining string
                    fp.close()
            elif event.type == pygame.JOYBUTTONUP:
                i = event.dict['button']
                Buttons[i] = 0
                my_logger.debug("Button {} released".format(i))
            elif event.type == pygame.JOYHATMOTION:
                Hat = event.dict['value']
                my_logger.debug("Hat value: {}".format(str(Hat)))
                my_logger.info("Hat[0] {} and Hat[1] {} ".format(Hat[0],Hat[1]))
                if Hat[1] == -1:     #Flicking Hat away from you for a new ycb object
                    my_ycb_object = cd.ycb_object_dataset(my_dataset)
                if Hat[0] == -1:
                    if my_dataset.empty:
                        my_logger.debug("No YCB object")
                    else:
                        one_datafile = cd.data(my_ycb_object)
                        finger_file = one_datafile.filename
                        my_logger.info("*****Data file for Grabber Finger positions {}:".format(finger_file))
                        if old_datafile: #closing the previous data file before starting the next
                            finger_file_fp.close()
                        try:
                            finger_file_fp = open(one_datafile.filename,"w")
                            old_datafile = finger_file
                        except IOError:
                            my_logger.info("Failure to File {}:".format(finger_file))
                            raise IOError ("Unable to open file for Grabber Finger position recording")

                        finger_file_fp.write("Data file: "+finger_file+"\n")
                        palm.move_to_rest_position()
                        set_record = 1

                        t1 = datetime.now()
                        F = palm.get_palm_current_position()
                        t2 = datetime.now()
                        t = (t2-t1)
                        my_logger.info("Time T1: {} T2: {} Diff s:{} microsecond:{} "\
                                       .format(t1,t2,t.seconds,t.microseconds))

                        my_logger.info("Finger Rest Positions F1-{} F2-{} F3-{} F4-{}".format(F[1],F[2],F[3],F[4]))
                        finger_file_fp.write("Start position\n")
                        finger_file_fp.write("F1-"+ str(F[1])+",F2-"+str(F[2])+",F3-"+ str(F[3])+",F4-"+str(F[2])+"\n")
                        if my_cam.camera == 1:
                            if my_cam.capture_and_save_frame(finger_file) == 0:
                                my_logger.info("Camera read of image file write failure : ".format(finger_file))
                            else:
                                my_logger.info("Image file created :{}"+".png".format(finger_file))
                        else:
                            my_logger.info("Camera setting failure : ".format(finger_file))
                        my_command.start_collecting(finger_file)
                if Hat[0] == 1:
                    if set_record == 1:
                        F = palm.get_palm_current_position()
                        my_logger.info("Grabber position F1-{} F2-{} F3-{} F4-{}".format(F[1],F[2],F[3],F[4]))
                        finger_file_fp.write("End position\n")
                        finger_file_fp.write("F1-"+ str(F[1])+",F2-"+str(F[2])+",F3-"+ str(F[3])+",F4-"+str(F[2])+"\n")
                        F = palm.read_servo_current_location()
                        my_logger.info("Servo position M1-{} M2-{} M3-{} M4-{}".format(F[1],F[2],F[3],F[4]))
                        finger_file_fp.write("M1-"+ str(F[1])+",M2-"+str(F[2])+",M3-"+ str(F[3])+",M4-"+str(F[2])+"\n")
                        set_record = 0
                        my_command.stop_collecting()
                    else:
                        pass
            else:
                pass # ignoring other event types

        # Event less state monitoring of Joy axis positions
        for k in range(0, Num_Axes, 1):
            Axes[k] = j_device.joystick.get_axis(k)
            if Axes[k] > 0:
                if Axes[k] > max_val[k]:
                    direction[k] = 1
                    move_goal[k] = int(Axes[k]*MOVE_TICKS)
                    if k == 1:
                        joy_move[1] = 1
                    elif k == 0:
                        joy_move[0] = 1
                    elif k == 3:
                        if A3_palm_position_reporting:
                            F = palm.get_rest_position()
                            my_logger.info("Rest Position F1-{}, F2-{}, F3-{}, F4-{}".format(F[1],F[2],F[3],F[4]))
                            F = palm.get_palm_current_position()
                            my_logger.info("Current Position F1-{}, F2-{}, F3-{}, F4-{}".format(F[1],F[2],F[3],F[4]))
                            F= palm.get_max_position()
                            my_logger.info("Max Position F1-{}, F2-{}, F3-{}, F4-{}".format(F[1],F[2],F[3],F[4]))
                            A3_palm_position_reporting = 0
                        else:
                            pass    # not logging A3_palm_position
                    else:
                        pass    # end of checking k values (0,1,3) for positive displacement
            elif Axes[k] < 0:
                if Axes[k] < min_val[k]:
                    direction[k] = -1
                    move_goal[k] = int(abs(Axes[k])*MOVE_TICKS)
                    if k == 1:
                        joy_move[1]=1
                    elif k == 0:
                        joy_move[0]=1
                    elif k==3:
                        palm_position_reporting = 1
                    else:
                        pass # end of checking k values (0,1,3) for negative displacement
            else:
                pass

        k = 1   #Servo 1,2,3
        if joy_move[k] == 1:
            joy_move[k] = 0
            my_logger.info("Joy Axis displacement: {}, Direction: {}, M1-M2-M3 moveby: {}".
                           format(Axes[k], direction[k], move_goal[k]))
            if old_datafile:
                palm.grip_fingers(move_goal[k],direction[k],set_record,finger_file_fp)
            else:
                palm.grip_fingers(move_goal[k],direction[k])

        k = 0   #Servo 4
        if joy_move[k] == 1:
            joy_move[k] = 0
            my_logger.info("Joy Axis displacement: {}, Direction: {}, M4 moveby: {}".
                           format(Axes[k], direction[k], move_goal[k]))
            if old_datafile:
                palm.space_finger1_and_finger2(move_goal[k],direction[k],set_record,finger_file_fp)
            else:
                palm.space_finger1_and_finger2(move_goal[k],direction[k])


        textPrint.Screenprint(screen, "Joystick name: {}".format(j_device.name))
        textPrint.Yspace()
        textPrint.Screenprint(screen, "Number of Axes: {}".format(Num_Axes))
        textPrint.indent()
        for i in range(Num_Axes):
            textPrint.Screenprint(screen, "Axis {} value: {:>6.3f}".format(i, Axes[i]))
        textPrint.unindent()
        textPrint.Yspace()
        textPrint.Screenprint(screen, "Number of Buttons: {}".format(Num_Buttons))
        textPrint.indent()
        for i in range(Num_Buttons):
            textPrint.Screenprint(screen, "Button {:>2} value: {}".format(i,Buttons[i]))
        textPrint.unindent()
        textPrint.Yspace()
        textPrint.Screenprint(screen, "Number of Hats: {}".format(Num_Hats) )
        textPrint.indent()
        textPrint.Screenprint(screen, "Hat value: {}".format(str(Hat)) )
        textPrint.unindent()


    # ALL CODE TO DRAW SHOULD GO ABOVE THIS COMMENT

    # Go ahead and update the screen with what we've drawn.
        pygame.display.flip()

    # Limit to 20 frames per second OR 50 ms scan rate - 1000/20 = 50 ms Both display and checking of Joystick;
        clock.tick(SCAN_RATE)
# Close the window and quit.
# If you forget this line, the program will 'hang' on exit if running from IDLE.

my_cam.close_video()
pygame.quit ()
if old_datafile:        #when no batch is created, the program won't try to close a non-existant file handle
    finger_file_fp.close()
my_command.destroy()    #close socket






