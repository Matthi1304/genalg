DUMMY = True


class FitnessFunction():

    def __init__(self, app):
        self.app = app


    def _hour_fitness(self, image, hour):
        # Analyze the image to compute fitness contribution for this hour
        from random import random
        return random()


    def fitness_function(self, individual):
        if DUMMY:
            from random import random
            return random()
        fitness = 0.0
        self.app.set_configuration(individual)
        for hour in range(12):
            image = self.app.make_screenshot(hour=hour)
            fitness += self._hour_fitness(image, hour)
        return fitness / 12.0