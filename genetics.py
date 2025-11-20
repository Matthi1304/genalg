from random import random, randint, sample
import os
import json
import sys
import visualization
from fitness import FitnessFunction
from dotenv import load_dotenv
from random import random, randint

RADIUS = 15000.0

DEFAULT_NUM_CHROMOSOMS = 100
DEFAULT_SIZE_OF_GENERATION = 50
DEFAULT_SURVIVOR_RATE = 0.3
DEFAULT_MUTATION_RATE = 0.1
DEFAULT_TOURNAMENT_SIZE = 100

class Genetics:

    def __init__(self, 
                 num_chromosoms=DEFAULT_NUM_CHROMOSOMS, 
                 size_of_generation=DEFAULT_SIZE_OF_GENERATION,
                 survivor_rate=DEFAULT_SURVIVOR_RATE, 
                 mutation_rate=DEFAULT_MUTATION_RATE, 
                 tournament_size=DEFAULT_TOURNAMENT_SIZE):
        self.num_chromosoms = num_chromosoms
        self.size_of_generation = size_of_generation
        self.survivor_rate = survivor_rate
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size


    def run(self, app):
        fitness_function = FitnessFunction(app).fitness_function
        population = self.create_random_population()
        for generation in range(self.tournament_size + 1):
            print(f"Generation {generation}")
            population_fitness = []
            for individual in population:
                fitness = fitness_function(individual)
                population_fitness.append((fitness, individual))
            population_fitness.sort(key=lambda x: x[0], reverse=True)
            num_survivors = int(self.size_of_generation * self.survivor_rate)
            survivors = [ind for _, ind in population_fitness[:num_survivors]]
            print(f"  Best fitness:           {population_fitness[0][0]}")
            print(f"  Worst survivor fitness: {population_fitness[num_survivors-1][0]}")
            print(f"  Worst fitness:          {population_fitness[-1][0]}")
            print(f"  Average fitness:        {sum(f for f, _ in population_fitness) / len(population_fitness)}")
            if generation == self.tournament_size:
                # store the best individual
                self.winner = survivors[0]
                return
            new_population = []
            new_population.append(survivors[0])  # Elitism: carry over the best individual
            while len(new_population) < self.size_of_generation:
                child = self.crossover(sample(survivors, 3))
                new_population.append(child)
            for m in range(int(self.size_of_generation * self)):
                individual = new_population[randint(0,  self.size_of_generation - 1)]
                self.mutate(individual)
            population = new_population


    def crossover(self, parents):
        # We can do a N-way crossover by taking some chromosoms from each parent.
        # For example, if we have 100 chromosoms, we can take 33 to 34 chromosoms for N=3 parent.
        # Note that NUM_CHROMOSOMS may not be exactly divisible by N.
        # We should randomly select which chromosoms to take from each parent.
        # Make sure the resulting child has the same number chromosoms as it's parents.
        # We assume all parents have the same number of chromosoms.
        child = []
        count = int(len(parents[0]) / len(parents))
        while parents: 
            parent = parents.pop(0)
            num_to_take = count if parents else len(parent) - len(child)
            child += sample(parent, num_to_take)
        return child


    def mutate(self, individual):
        # We can mutate by replacing one chromosom with a new random one, 
        # or by changing one of its parameters.
        # Parameters are: [digit, x, y, z, size, heading_degrees].
        # Each parameter should should mutate with equal probability.
        # A mutation should be small, e.g. position +/- 1000, size +/- 100, heading +/- 10 degrees.
        # Make sure to keep parameters within valid ranges
        index = randint(0, len(individual) - 1)
        choice = random()
        if choice < 0.2:
            # Replace a chromosom
            individual[index] = create_random_chromosom()
        else:
            # Mutate a parameter
            param_index = randint(0, 5)
            chromosom = individual[index]
            if param_index == 0:
                chromosom[0] = randint(0, 9)
            elif param_index in [1, 2, 3]:
                chromosom[param_index] += randint(-1000, 1000)
                chromosom[param_index] = max(-RADIUS, min(RADIUS, chromosom[param_index]))
            elif param_index == 4:
                chromosom[4] += randint(-100, 100)
                chromosom[4] = max(1, min(10000, chromosom[4]))
            elif param_index == 5:
                chromosom[5] += randint(-10, 10)
                chromosom[5] = chromosom[5] % 360


    def create_random_population(self):
        population = []
        for _ in range(self.size_of_generation):
            individual = self.create_random_individual()
            population.append(individual)
        return population


    def create_random_individual(self):
        individual = []
        for _ in range(self.num_chromosoms):
            chromosom = create_random_chromosom()
            individual.append(chromosom)
        return individual


def create_random_chromosom():
    # [digit, x, y, z, size, heading_degrees]
    return [randint(0, 9)] + _random_point_in_sphere(RADIUS) + [randint(1, 10000), randint(0, 359)]


def _random_point_in_sphere(radius):
    while True:
        x = random() * 2 - 1
        y = random() * 2 - 1
        z = random() * 2 - 1
        if x*x + y*y + z*z <= 1:
            return [int(x * radius), int(y * radius), int(z * radius)]


def _get_from_env(var_name, default, cast_type):
    value = os.getenv(var_name)
    if value is None:
        print(f"Info: Using default value for {var_name}={default}.")
    else:
        try:
            value = cast_type(value)
            print(f"Info: Setting value for {var_name}={value} from .env or environment (precedence).")
            return value
        except ValueError:
            print(f"Warning: Could not cast environment variable {var_name}='{value}' to {cast_type}. Using default {default}.")
    return default




if __name__ == "__main__":
    load_dotenv()
    NUM_CHROMOSOMS = _get_from_env("NUM_DIGITS", 100, int)
    SIZE_OF_GENERATION = _get_from_env("SIZE_OF_GENERATION", 50, int)
    SURVIVOR_RATE = _get_from_env("SURVIVOR_RATE", 0.3, float)
    MUTATION_RATE = _get_from_env("MUTATION_RATE", 0.1, float)
    TOURNAMENT_SIZE = _get_from_env("TOURNAMENT_SIZE", 100, int)
    genetics = Genetics(
        num_chromosoms=NUM_CHROMOSOMS,
        size_of_generation=SIZE_OF_GENERATION,
        survivor_rate=SURVIVOR_RATE,
        mutation_rate=MUTATION_RATE,
        tournament_size=TOURNAMENT_SIZE
    )
    visualization.headless_app(callback=genetics)
