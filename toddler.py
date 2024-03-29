#!/usr/bin/env python
__TODDLER_VERSION__ = '1.0.0'

import time

from robot.body.motors import Motors
from robot.body.sensors import Sensors
from robot.vision.vision import Vision
from robot.state.particle_filtering import Particles, Y_MAX, X_MAX
from robot.visualisation.drawing import Drawing
from robot.milestone2_1_logic import milestone2
from robot.localization_logic import wander_and_travel


import numpy as np

POSE_MY_PARTICLES = [162, Y_MAX-108, 3.0/2.0*np.pi]
POSE_TEST_CORNERROOM = [143+18, 77, np.pi/2.]
POSE_TEST_MIDDLEROOM = [X_MAX-71, Y_MAX-(132+39), np.pi/2.]
POSE_TEST_MILESTONE2 = [X_MAX-110, 231-46-50, 0]

# TODO: sanity check jumping between rooms
# TODO: DITTO WHAT YOU MEAN BRO, COMPLETELY SANE
class Toddler:
    def __init__(self, io):
        print 'Toddler, the dragon has awoken... Beware.'
        self.io = io
        self.sensors = Sensors(io)
        self.motors = Motors(io, self.sensors)
        self.vision = Vision(io)
        self.particles = Particles(n=250, where='set', drawing=Drawing(), pose=POSE_TEST_MILESTONE2)

    def stop(self):
        """For development only"""
        time.sleep(1000)

    # This is a callback that will be called repeatedly.
    # It has its dedicated thread so you can keep block it.
    def Control(self, ok):
        while ok():
            self.motors.turn_by_revs(1)
            # self.motors.go_forward_revs(1)
            self.stop()
            #milestone2(self.sensors, self.motors, self.vision, self.particles)
            # perform_basic_milestone(self.sensors, self.motors)
            # wander_and_travel(self.sensors, self.particles, self.motors, self.vision)
            # collect_front_IR_and_sonar_measurements(self.io)

    # This is a callback that will be called repeatedly.
    # It has its dedicated thread so you can keep block it.
    def Vision(self, ok):
        while ok():
            pass
            # self.vision.do_image()
