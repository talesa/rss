"""
Port mapping

0: front IR sensor
1: right IR sensor
"""


def ir_input_to_distance(voltage):
    ir_max = 110
    return_max_value = 256
    try:
        value = 4800. / (voltage - 20.)
    except ZeroDivisionError:
        return ir_max
    if value > ir_max:
        value = return_max_value
    return value if value > 0 else return_max_value

def sensor_input_to_distance(voltage):
    sensor_max = 640.0
    value = voltage * 1.296
    if value > sensor_max:
        value = sensor_max
    return value

class Sensors:
    def __init__(self, io):
        self.analogue = 10 * [None]
        self.io = io

    def get_analogue(self):
        self.analogue = self.io.getSensors()

    def get_ir_front_raw(self):
        """
        :rtype : float
        """
        self.get_analogue()
        return self.analogue[0]

    def get_ir_front(self):
        return ir_input_to_distance(self.get_ir_front_raw())

    def get_ir_right_raw(self):
        """
        :rtype : float
        """
        self.get_analogue()
        return self.analogue[1]

    def get_ir_right(self):
        return ir_input_to_distance(self.get_ir_right_raw())

    def get_sonar_raw(self):
        """
        :rtype : float
        """
        self.get_analogue()
        return self.analogue[2]

    def get_sonar(self):
        """
        :rtype : float
        """
        self.get_analogue()
        return sensor_input_to_distance(self.analogue[2])

    def get_irs(self):
        self.get_analogue()
        return [ir_input_to_distance(self.analogue[0]),
                ir_input_to_distance(self.analogue[1])]

    def get_irs_and_sonar(self):
        self.get_analogue()
        return [ir_input_to_distance(self.analogue[0]),
                ir_input_to_distance(self.analogue[1]),
                sensor_input_to_distance(self.analogue[2])]


class SensorRunningAverage:
    # TODO: values should expire if new are not added
    def __init__(self, number_of_values=5, init_value=20):
        self.number_of_values = number_of_values
        self.values = number_of_values * [init_value]

    def add_value(self, new_value):
        """Dismisses oldest, adds new one at the end
        """
        new_value = 81 if new_value is None else new_value
        self.values = self.values[1:] + [new_value]

    def get_avg(self):
        """Arithmetic average
        """
        return sum(self.values) / self.number_of_values
