from __future__ import division

import numpy as np
import random
import math
from math import pi
from state.map import X_MAX, Y_MAX, ARENA_WALLS
import utils


ROTATION_STD_ABS = (5.0 / 360.0) * 2.0 * math.pi
DRIFT_ROTATION_STD_ABS = (1.0 / 360.0) * 2.0 * math.pi
FORWARD_STD_FRAC = 0.1

# edge r to r+s, tuples in the (r, s) format, not (r, r+s)
ROBOT_EDGES = [
    ([-11.0, -13.0], [0.0, 26.0]),
    ([-11.0, 13.0], [32.0, 0.0]),
    ([21.0, 13.0], [0.0, -26.0]),
    ([21.0, -13.0], [-32.0, 0.0])
]

SENSORS_LOCATIONS = {
    'IR_front': {'location': [0.0, 21.0], 'orientation': 0.0},
    'IR_right': {'location': [7.5, 15.0], 'orientation': pi / 2.0},
    'sonar_front': {'location': [0.0, 21.0], 'orientation': 0.0},
}

MAX_BEAM_RANGE = math.sqrt(2.0 * ((5 * 106.5) ** 2))

X_BASE_OFFSET = 10
Y_BASE_OFFSET = 10
X_BASE_LENGTH = 30
Y_BASE_LENGTH = 50

class Particles:
    def __init__(self, n=100, where=None, drawing=None):
        """
        Creates particle set with given initial position
        :param n: number of particles
        :return:
        """
        self.N = n
        self.drawing = drawing

        if where == 'bases':
            a = (np.array([X_BASE_OFFSET, Y_BASE_OFFSET])
                 + np.multiply(np.array([X_BASE_LENGTH, Y_BASE_LENGTH]), np.random.rand(self.N/2, 2)))\
                .astype(np.int16)
            b = (np.array([X_MAX - X_BASE_OFFSET, Y_MAX - Y_BASE_OFFSET])
                 - np.multiply(np.array([X_BASE_LENGTH, Y_BASE_LENGTH]), np.random.rand(self.N/2, 2)))\
                .astype(np.int16)
            self.locations = np.concatenate([a, b])
        else:
            self.locations = np.multiply(np.array([X_MAX, Y_MAX],dtype=np.float32), np.random.rand(self.N, 2)).astype(np.int16)

        self.orientations = np.multiply(np.array([2.0 * pi]), np.random.rand(self.N)).astype(np.float32)
        self.weights = np.ones(self.N, dtype=np.float32)

    def get_position_by_average(self):
        """
        :return: average of particle positions
        """

        x_approx = np.average(self.locations)
        y_approx = np.average(self.locations)
        o_approx = np.average(self.at_orientation())

        if self.drawing:
            for r in self.particles:
                self.drawing.add_point(r.x, r.y)
            self.drawing.add_big_point(x_approx, y_approx)
            self.drawing.save()

        return x_approx, y_approx, o_approx, self.get_position_conf()

    def get_position_conf(self):
        x_norm = 0
        y_norm = 0
        for i, particle in enumerate(self.particles):
            x_norm += (particle.x - .5 * X_MAX) * self.weights[i]
            y_norm += (particle.y - .5 * Y_MAX) * self.weights[i]
        x_norm /= X_MAX
        y_norm /= Y_MAX
        return .5 * (np.var(x_norm) + np.var(y_norm))

    def get_position_by_weight(self, position_confidence=True):
        """
        :return: highest weighted particle position
        """
        i = np.argmax(self.weights)
        x_approx, y_approx = self.locations[i]
        o_approx = self.orientations[i]
        if position_confidence:
            return x_approx, y_approx, o_approx, self.get_position_conf()
        else:
            return x_approx, y_approx, o_approx

    def rotate(self, rotation):
        """Rotates all the particles"""
        self.orientations = np.mod(
            np.add(
                self.orientations,
                np.add(
                    np.multiply(
                        np.random.rand(self.N),
                        ROTATION_STD_ABS
                    ),
                    -0.5*ROTATION_STD_ABS + rotation
                )
            ),
            2.0 * pi)\
            .astype(np.float32)

    def forward(self, distance):
        """Moves the particles forward"""
        #forward_inferred = random.gauss(distance, FORWARD_STD_FRAC * distance)
        # taking into account possible unintended rotation
        # TODO drift
        # rotation_inferred = random.gauss(0, ROTATION_STD_ABS)
        # orientation = (self.orientation + rotation_inferred) % (2.0 * math.pi)

        orientations = np.add(
            np.multiply(
                np.random.rand(self.N),
                DRIFT_ROTATION_STD_ABS
            ),
            self.orientations
        )

        vectors = np.concatenate([np.zeros((self.N,1)), np.ones((self.N,1))], axis=1)

        distances =\
        np.add(
            np.multiply(
                np.random.rand(self.N),
                FORWARD_STD_FRAC*distance
            ),
            (1-0.5*FORWARD_STD_FRAC)*distance
        )

        for i in xrange(len(vectors)):
            orientation = orientations[i]
            rot_matrix = np.array([
                [ np.cos(orientation), np.sin(orientation)],
                [-np.sin(orientation), np.cos(orientation)]
            ])
            vectors[i] = np.multiply(np.dot(rot_matrix, vectors[i]),distances[i])

        self.locations =\
            np.add(
                self.locations,
                vectors
            )

    def backward(self, distance):
        """Moves the particles backward"""
        self.forward(-distance)

    def sense(self, measurement):
        """Sensing"""
        probabilities = np.zeros(self.N, dtype=np.float32)
        for i in xrange(self.N):
            probabilities[i] = self.measurement_probability(measurement, self.measurement_prediction(i))

        self.weights = np.multiply(self.weights, probabilities)

    def resample(self):
        # TODO different resampling
        new_locations = np.zeros((self.N, 2), dtype=np.int16)
        new_orientations = np.zeros(self.N, dtype=np.float32)
        index = int(random.random() * self.N)
        beta = 0.0
        mw = max(self.weights)

        p3index = 0
        for i in range(self.N):
            beta += random.random() * 2.0 * mw
            while beta > self.weights[index]:
                beta -= self.weights[index]
                index = (index + 1) % self.N
            new_locations[p3index] = self.locations[index]
            new_orientations[p3index] = self.orientations[index]
            p3index += 1
        self.locations = new_locations
        self.orientations = new_orientations

        self.weights = np.ones(self.weights.shape).astype(np.float32)

    def location(self, i):
        """
        Returns a location vector
        :return: location vector [x, y]
        """
        return self.locations[i]

    def orientation(self, i):
        """
        Returns a location vector
        :return: location vector [x, y]
        """
        return self.orientations[i]

    def at_orientation(self, i, vectors):
        """
        Rotates the VECTORS by robot's orientation angle (measured from y axis clockwise)
        :param vectors:
        :return: rotated vectors
        """
        return utils.at_orientation(vectors, self.orientation(i))

    def is_collision(self, i):
        """
        Checks if the robot pose collides with an obstacle
        """
        for wall in ARENA_WALLS:
            for edge in ROBOT_EDGES:
                if utils.intersects(wall, self.location(i) + self.at_orientation(i, edge)):
                    return True
        return False

    def rotate_particle(self, i, rotation):
        """
        Infers true pose after rotation (draws from gaussian)
        :param rotation:
        :return: new particle
        """
        rotation_inferred = np.random.normal(rotation, ROTATION_STD_ABS)
        new_orientation = (self.orientation(i) + rotation_inferred) % (2.0 * math.pi)
        self.orientations[i] = new_orientation

    def forward_particle(self, i, distance):
        """
        Infers true coordinates and pose after forwards/backwards movement (draws from gaussian)
        :param distance:
        :return: new particle
        """
        forward_inferred = random.gauss(distance, FORWARD_STD_FRAC * distance)
        # taking into account possible unintended rotation
        # TODO drift
        # rotation_inferred = random.gauss(0, ROTATION_STD_ABS)
        # orientation = (self.orientation + rotation_inferred) % (2.0 * math.pi)
        orientation = self.orientation(i)

        location = utils.at_orientation(np.array([0, 1], dtype=np.float32), orientation) * forward_inferred

        x, y = np.add(location, self.location(i))

        # Prevent out of arena predictions
        x = 0 if x < 0 else x
        x = X_MAX-1 if x >= X_MAX else x

        y = 0 if y < 0 else y
        y = Y_MAX-1 if y >= Y_MAX else y

        self.particles[i] = np.array([x, y, orientation], dtype=np.float32)

    def measurement_prediction(self, i):
        """
        Finds measurement predictions based on particle location.
        :return: measurement predictions
        """

        beam_front = utils.at_orientation([0, MAX_BEAM_RANGE],
                                          self.orientation(i) + SENSORS_LOCATIONS['IR_front']['orientation'])
        beam_right = utils.at_orientation([0, MAX_BEAM_RANGE],
                                          self.orientation(i) + SENSORS_LOCATIONS['IR_right']['orientation'])
        front = np.add(self.location(i),
                       utils.at_orientation(SENSORS_LOCATIONS['IR_front']['location'],
                                            self.orientation(i)))
        right = np.add(self.location(i),
                       utils.at_orientation(SENSORS_LOCATIONS['IR_right']['location'],
                                            self.orientation(i)))

        # print 'Robot: ' + str(self.location(i)[0]) + ' ' + str(self.location(i)[1]) + ' ' + str(self.orientation(i))
        # print 'Sensors: ' + str(front) + str(right)
        # print 'Beams: ' + str(beam_front) + str(beam_right)

        # find distances to the closest walls
        distances = {}
        for sensor_location, beam, label in (front, beam_front, 'IR_front'), (right, beam_right, 'IR_right'):
            minimum_distance = MAX_BEAM_RANGE
            for wall in ARENA_WALLS:
                intersection = utils.intersects_at(wall, (sensor_location, beam))
                if intersection is not None:
                    distance = np.linalg.norm(np.subtract(intersection, sensor_location))
                    if distance < minimum_distance:
                        minimum_distance = distance
            distances[label] = minimum_distance

        return distances

    def measurement_probability(self, measurements, predictions):
        """
        Finds the measurements probability based on predictions.

        :param measurements: dictionary with 'IR_front' and 'IR_right'
        :param predictions: dictionary with 'IR_front' and 'IR_right'
        :return: probability of measurements
        """
        # TODO establish common labels

        weights = np.array([0.5, 0.5], dtype=np.float32)
        probabilities = np.array([self.measurement_prob_ir(measurements['IR_front'], predictions['IR_front']),
                                  self.measurement_prob_ir(measurements['IR_right'], predictions['IR_right'])],
                                 dtype=np.float32)
        return np.dot(weights, probabilities)

    @staticmethod
    def measurement_prob_ir(measurement, predicted):
        prob_hit_std = 5.0
        # if 10 < predicted < 80:
        prob_hit = math.exp(-(measurement - predicted) ** 2 / (prob_hit_std ** 2) / 2.0) \
                       / math.sqrt(2.0 * math.pi * (prob_hit_std ** 2))
        # else:
        #     prob_hit = 0

        unexpected_decay_const = 0.5
        if measurement < predicted:
            prob_unexpected = unexpected_decay_const * math.exp(-unexpected_decay_const * measurement) \
                              / (1 - math.exp(-unexpected_decay_const * predicted))
        else:
            prob_unexpected = 0

        prob_rand = 1 / MAX_BEAM_RANGE

        prob_max = 0.1 if predicted > 80 else 0

        weights = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        probabilities = np.array([prob_hit, prob_unexpected, prob_rand, prob_max],
                                 dtype=np.float32)
        return np.dot(weights, probabilities)


class Robot:
    """Only for keeping track of our real robot"""
    def __init__(self, x=0., y=0., orientation=0.):
        self.x = x
        self.y = y
        self.orientation = orientation

    def set(self, new_x, new_y, new_orientation):
        self.x = float(new_x)
        self.y = float(new_y)
        self.orientation = float(new_orientation) % (2.0 * math.pi)

    def location(self):
        """
        Returns a location vector
        :return: location vector [x, y]
        """
        return np.array([self.x, self.y])

    def at_orientation(self, vectors):
        """
        Rotates the VECTORS by robot's orientation angle (measured from y axis clockwise)
        :param vectors:
        :return: rotated vectors
        """
        return utils.at_orientation(vectors, self.orientation)

    def is_collision(self):
        """
        Checks if the robot pose collides with an obstacle
        """
        for wall in ARENA_WALLS:
            for edge in ROBOT_EDGES:
                if utils.intersects(wall, self.location() + self.at_orientation(edge)):
                    return True
        return False

    def rotate(self, rotation):
        """
        Infers true pose after rotation (draws from gaussian)
        :param rotation:
        :return: new particle
        """
        rotation_inferred = random.gauss(rotation, ROTATION_STD_ABS)
        orientation = (self.orientation + rotation_inferred) % (2.0 * math.pi)
        return Robot(x=self.x, y=self.y, orientation=orientation)

    def forward(self, distance):
        """
        Infers true coordinates and pose after forwards/backwards movement (draws from gaussian)
        :param distance:
        :return: new particle
        """
        forward_inferred = random.gauss(distance, FORWARD_STD_FRAC * distance)
        # taking into account possible unintended rotation
        rotation_inferred = random.gauss(0, ROTATION_STD_ABS)
        orientation = (self.orientation + rotation_inferred) % (2.0 * math.pi)

        location = utils.at_orientation([0, 1], orientation) * forward_inferred

        x, y = np.add(location, self.location())

        # Prevent out of arena predictions
        x = 0 if x < 0 else x
        x = X_MAX-1 if x >= X_MAX else x

        y = 0 if y < 0 else y
        y = X_MAX-1 if y >= Y_MAX else y

        return Robot(x=x, y=y, orientation=orientation)

    def measurement_prediction(self):
        """
        Finds measurement predictions based on particle location.
        :return: measurement predictions
        """

        beam_front = utils.at_orientation([0, MAX_BEAM_RANGE],
                                          self.orientation + SENSORS_LOCATIONS['IR_front']['orientation'])
        beam_right = utils.at_orientation([0, MAX_BEAM_RANGE],
                                          self.orientation + SENSORS_LOCATIONS['IR_right']['orientation'])
        front = np.add(self.location(), SENSORS_LOCATIONS['IR_front']['location'])
        right = np.add(self.location(), SENSORS_LOCATIONS['IR_right']['location'])

        #
        # print front, right
        # print beam_front, beam_right


        # find distances to the closest walls
        distances = {}
        for sensor_location, beam, label in (front, beam_front, 'IR_front'), (right, beam_right, 'IR_right'):
            minimum_distance = MAX_BEAM_RANGE
            for wall in ARENA_WALLS:
                intersection = utils.intersects_at(wall, (sensor_location, beam))
                if intersection is not None:
                    distance = np.linalg.norm(np.subtract(intersection, sensor_location))
                    if distance < minimum_distance:
                        minimum_distance = distance
            distances[label] = minimum_distance

        return distances

    def measurement_probability(self, measurements, predictions):
        """
        Finds the measurements probability based on predictions.
        :param measurements: dictionary with 'IR_front' and 'IR_right'
        :param predictions: dictionary with 'IR_front' and 'IR_right'
        :return: probability of measurements
        """
        # TODO establish common labels

        weights = np.array([0.5, 0.5])
        probabilities = np.array(
            [weights[0] * self.measurement_prob_ir(measurements['IR_front'], predictions['IR_front']),
             weights[1] * self.measurement_prob_ir(measurements['IR_right'], predictions['IR_right'])])
        return np.dot(weights, probabilities)

    @staticmethod
    def measurement_prob_ir(measurement, predicted):
        prob_hit_std = 5.0
        if 10 < predicted < 80:
            prob_hit = math.exp(-(measurement - predicted) ** 2 / (prob_hit_std ** 2) / 2.0) \
                       / math.sqrt(2.0 * math.pi * (prob_hit_std ** 2))
        else:
            prob_hit = 0

        prob_unexpected_decay_const = 0.5
        if measurement < predicted:
            prob_unexpected = prob_unexpected_decay_const * math.exp(-prob_unexpected_decay_const * measurement) \
                              / (1 - math.exp(-prob_unexpected_decay_const * predicted))
        else:
            prob_unexpected = 0

        prob_rand = 1 / MAX_BEAM_RANGE

        prob_max = 0.2 if predicted > 80 else 0

        weights = np.array([0.7, 0.1, 0.1, 0.1])
        probabilities = np.array([prob_hit,prob_unexpected,prob_rand,prob_max])
        return np.dot(weights, probabilities)

    def __repr__(self):
        return '[x=%.5f y=%.5f orient=%.5f]' % (self.x, self.y, self.orientation)