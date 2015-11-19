from robot.utils import log
from robot.body.motors import HALL_ANGLE, HALL_PERIMETER
import numpy as np
from odometry_localisation import OdometryLocalisation
from utils import orientate, euclidean_distance
from robot.state.map import NODES_MILESTONE2_CORNERROOM

TARGET_CUBE = 'watching'

nodes = NODES_MILESTONE2_CORNERROOM
# nodes = [
#     {'coord': (1, 2), 'angle': 70}
# ]
#
# NODES_MILESTONE2_CORNERROOM = {
#     '1': {'id': '1', 'room': 'A', 'y': 48,          'x': X_MAX-54,      'ambiguous': False, 'connects': ['2', '8']},
#     '2': {'id': '2', 'room': 'A', 'y': 31,          'x': X_MAX-177+40,  'ambiguous': False, 'connects': ['1', '3']},
#     '3': {'id': '3', 'room': 'A', 'y': 70,          'x': X_MAX-177+55,  'ambiguous': True,  'connects': ['2', '4']},
#     '4': {'id': '4', 'room': 'A', 'y': 231-46-61,   'x': X_MAX-113,     'ambiguous': True,  'connects': ['3', '5']},
#     '5': {'id': '5', 'room': 'A', 'y': 231-69,      'x': X_MAX-81,      'ambiguous': True,  'connects': ['4', '6']},
#     '6': {'id': '6', 'room': 'A', 'y': 231-40,      'x': X_MAX-93+38,   'ambiguous': True,  'connects': ['5', '7']},
#     '7': {'id': '7', 'room': 'A', 'y': 231-55,      'x': X_MAX-31,      'ambiguous': False, 'connects': ['6', '8']},
#     '8': {'id': '8', 'room': 'A', 'y': 135,         'x': X_MAX-41,      'ambiguous': False, 'connects': ['7', '1']},
# }

def S5_just_go(motors, sensors, vision, particles):
    motors.go_forward(15*HALL_PERIMETER)
    particles.forward(15*HALL_PERIMETER)
    particles_measure_sense_resample(sensors, particles)
    while True:
        # ir_left = sensors.get_ir_left()
        # ir_right = sensors.get_ir_right()
        for key in sorted(nodes.keys()):
            node = nodes[key]
            x, y = (node['x'], node['y'])
            my_x, my_y, my_angle = particles.get_position_by_weighted_average()
            log('I believe I am at pose: x={}, y={}, o={}'.format(my_x,my_y,my_angle))
            log('Going to node {}'.format(key))
            log('Node coordinates: x={}, y={}'.format(x, y))
            turn_angle = orientate({'x': x, 'y': y}, my_x, my_y, my_angle)
            log('Turn angle: {}'.format(turn_angle))

            motors.turn_by(-turn_angle, full=True)
            particles.rotate(-turn_angle)
            particles_measure_sense_resample(sensors, particles)

            d = euclidean_distance((x, y), (my_x, my_y))

            motors.go_forward(d)
            particles.forward(d)
            particles_measure_sense_resample(sensors, particles)

            for i in xrange(int(2. * np.pi / HALL_ANGLE)):
                resources = vision.see_resources(TARGET_CUBE)
                if TARGET_CUBE in resources and resources[TARGET_CUBE]:
                    print TARGET_CUBE, 'found!'
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

    log('Measurement predictions: {}'
    .format(particles.measurement_prediction_explicit(np.array([x, y]), o)))
    particles.sense(measurements)
    particles.resample()
    particles.get_position_by_weighted_average()

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
