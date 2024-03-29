from robot.utils import log
from robot.body.motors import HALL_ANGLE, HALL_PERIMETER
import numpy as np
from odometry_localisation import OdometryLocalisation
from utils import orientate, euclidean_distance
from robot.state.map import NODES_MILESTONE2_CORNERROOM, NODES_MILESTONE2_MIDDLEROOM
from vision.calculations import correct_orientation_angle

TARGET_CUBE = 'mario'
DIST_CONST = 20
X = 143+33
Y = 77
ANGLE = np.pi/2  # degrees

nodes = NODES_MILESTONE2_CORNERROOM


def correct_orientation(mean, motors):
    turn_angle = correct_orientation_angle(mean, (800.0, 600.0))
    log(u'Turning towards the resource by {0:.2f}\N{DEGREE SIGN}'.format(round(turn_angle * 180. / np.pi, 2)))
    motors.turn_by(turn_angle)

# nodes = NODES_MILESTONE2_MIDDLEROOM
nodes = NODES_MILESTONE2_CORNERROOM

def S5_just_go(motors, sensors, vision, particles):
    motors.go_forward(15*HALL_PERIMETER)
    particles.forward(15*HALL_PERIMETER)
    particles_measure_sense_resample(sensors, particles)

    # motors.go_forward(15*HALL_PERIMETER)
    # particles.forward(15*HALL_PERIMETER)
    # particles_measure_sense_resample(sensors, particles)

    motors.turn_by(5./2.*np.pi)
    particles.rotate(5./2.*np.pi)

    particles_measure_sense_resample(sensors, particles)

    while True:
        # ir_left = sensors.get_ir_left()
        # ir_right = sensors.get_ir_right()
        for key in ['5', '7', '8', '1', '2', '3', '4', '5']:
            node = nodes[key]
            x, y = (node['x'], node['y'])
            my_x, my_y, my_angle = particles.get_position_by_weighted_average()
            log('I believe I am at pose: x={}, y={}, o={}'.format(my_x,my_y,my_angle))
            log('Going to node {}'.format(key))
            log('Node coordinates: x={}, y={}'.format(x, y))
            turn_angle = orientate({'x': x, 'y': y}, my_x, my_y, my_angle)
            log('Turn angle: {}'.format(turn_angle))

            #TODO full = ?
            motors.turn_by(turn_angle, full=False)
            particles.rotate(turn_angle)
            particles_measure_sense_resample(sensors, particles)

            # d = euclidean_distance((x, y), (my_x, my_y))
            # d2 = d / 2.0
            # motors.go_forward(d2)
            # particles.forward(d2)
            #
            # particles_measure_sense_resample(sensors, particles)
            # my_x, my_y, my_angle = particles.get_position_by_weighted_average()
            # log('I believe I am at pose: x={}, y={}, o={}'.format(my_x,my_y,my_angle))
            # log('Going to node {}'.format(key))
            # log('Node coordinates: x={}, y={}'.format(x, y))
            # turn_angle = orientate({'x': x, 'y': y}, my_x, my_y, my_angle)
            #
            # motors.turn_by(turn_angle, full=False)
            # particles.rotate(turn_angle)
            # particles_measure_sense_resample(sensors, particles)

            d = euclidean_distance((x, y), (my_x, my_y))

            motors.go_forward(d)
            particles.forward(d)
            particles_measure_sense_resample(sensors, particles)

            for i in xrange(int(2. * np.pi / HALL_ANGLE)):
                resources = vision.see_resources(TARGET_CUBE)
                if TARGET_CUBE in resources and resources[TARGET_CUBE]['found']:
                    log(TARGET_CUBE + ' found!')
                    # correct_orientation(resources[TARGET_CUBE]['mean'], motors)
                    # motors.move(100, 100)
                    # while sensors.get_ir_left_raw() > 15:
                    #     pass
                    # motors.halt()
                    motors.go_forward_revs(5)
                    log('I believe I captured {}'.format(TARGET_CUBE))
                    while True:
                        pass
                motors.turn_by(HALL_ANGLE)
                particles.rotate(HALL_ANGLE)
                particles_measure_sense_resample(sensors, particles)

        # resources = vision.see_resources(TARGET_CUBE)
        # if TARGET_CUBE in resources and resources[TARGET_CUBE]:
        #     print TARGET_CUBE, 'found!'
        # if (ir_left < DIST_CONST) and (ir_right < DIST_CONST) or ir_right > 60 and ir_left > 60:
        #     motors.go_forward(4*HALL_PERIMETER)
        #     resources = vision.see_resources()
        #     if TARGET_CUBE in resources and resources[TARGET_CUBE]:
        #         print TARGET_CUBE, 'found!'
        # motors.turn_by(HALL_ANGLE)

def particles_measure_sense_resample(sensors, particles):
    # localization - driving around avoiding obstacles
    left_ir_reading = sensors.get_ir_left()
    right_ir_reading = sensors.get_ir_right()
    sonar_reading = sensors.get_sonar()

    # Update position via particle filter
    measurements = {
        'IR_left': left_ir_reading if left_ir_reading is not None else 0,
        'IR_right': right_ir_reading if right_ir_reading is not None else 0,
        'sonar': sonar_reading if sonar_reading is not None else 0,
    }

    particles.sense(sensors.get_irs_raw())
    particles.resample()
    x,y,o = particles.get_position_by_weighted_average()
    log('Measurement predictions: {}'
    .format(particles.measurement_prediction_explicit(np.array([x, y]), o)))
    log('Measurements actual: {}'.format(measurements))

def milestone2(sensors, motors, vision, particles):
    state = {
        'mode': 'S5_just_go'
    }
    while True:
        if state['mode'] == 'S5_just_go':
            log('S5_just_go')
            S5_just_go(motors, sensors, vision, particles)
        else:
            raise Exception('Unknown state {0}'.format(state['mode']))
