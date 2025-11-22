from random import random, randint, sample
import os
import json
import sys
from time import time
from math import sqrt, sin, cos, pi
import visualization
from fitness import FitnessFunction
from dotenv import load_dotenv
from random import random, randint

RADIUS = 15000
QUANTIZATION = 100
Q = RADIUS // QUANTIZATION # the following condition should hold: Q * QUANTIZATION == RADIUS 

MAX_SCALE = 6000
MIN_SCALE =  500

NUM_PARENTS = 3 # must be at least 2

DEFAULT_NUM_CHROMOSOMS = 100
DEFAULT_SIZE_OF_GENERATION = 50
DEFAULT_SURVIVOR_RATE = 0.3
DEFAULT_MUTATION_RATE = 0.1
DEFAULT_TOURNAMENT_SIZE = 100

class Individual:

    def __init__(self, genom):
        self.genom = genom
        self.fitness = None


    def _random_point():
        # Blender (and Panda3d) uses a right-angled “Cartesian” coordinate system with the Z axis pointing upwards.
        # X axis - Left / Right
        # Y axis - Front / Back
        # Z axis - Top / Bottom

        # z = randint(-Q, Q) * QUANTIZATION
        while True:
            x = random() * 2 - 1
            y = random() * 2 - 1
            z = random() * 2 - 1
            if x*x + y*y + z*z <= 1:
                return (int(x * Q) * QUANTIZATION, int(y * Q) * QUANTIZATION, int(z * Q) * QUANTIZATION)


    def create_random_gene():
        # [digit, x, y, z, size, heading_degrees]
        x, y, z = Individual._random_point()
        return [randint(0, 9), x, y, z, randint(MIN_SCALE, MAX_SCALE), randint(0, 359)]


    @staticmethod
    def random_individual(size_of_genom):
        genom = [Individual.create_random_gene() for _ in range(size_of_genom)]
        return Individual(genom)
    

    @staticmethod
    def breed(parents):
        # We can do a N-way crossover by taking similar amount of genes from each parent.
        # For example, if we have 100 genes, we can take 33 to 34 genes for N=3 parents.
        # Note that number of genes per genome may not be exactly divisible by N.
        # We should randomly select which genes to take from each parent.
        # Make sure the resulting child has the same number genes as it's parents.
        # We assume all parents have the same number of genes.
        childGenom = []
        genes_per_parent = int(len(parents[0].genom) / len(parents))
        while parents: 
            parent = parents.pop(0)
            number_of_genes = genes_per_parent if parents else len(parent.genom) - len(childGenom)
            childGenom += sample(parent.genom, number_of_genes)
        return Individual(childGenom)


    def getFitness(self, fitness_function=None):
        if self.fitness is None:
            if fitness_function is None:
                raise ValueError("Fitness function must be provided for fitness evaluation.")
            self.fitness = fitness_function(self.genom)
        return self.fitness


    def mutate(self):
        # We can mutate by replacing one gene with a new random one, 
        # or by mutate an individual gene.
        # A gene has six parameters: [digit, x, y, z, size, heading_degrees].
        # Each parameter should should mutate with equal probability.
        # A mutation should be small, e.g. position +/- 1000, size +/- 100, heading +/- 20 degrees.
        # Make sure to keep parameters within valid ranges
        self.fitness = None  # reset cached fitness
        index = randint(0, len(self.genom) - 1)
        choice = random()
        if choice < 0.2:
            # Replace a chromosom
            self.genom[index] = Individual.create_random_gene()
        else:
            # Mutate a parameter
            #  0      1  2  3  4     5
            # [digit, x, y, z, size, heading_degrees]
            pos = randint(0, 5)
            gene = self.genom[index]
            if pos == 0:
                gene[0] = randint(0, 9)
            elif pos in [1, 2, 3]:
                # todo: we could do a better job here to ensure we stay within the target space
                gene[pos] += randint(-1000, 1000)
                gene[pos] = max(-RADIUS, min(RADIUS, gene[pos]))
            elif pos == 4:
                gene[4] += randint(-100, 100)
                gene[4] = max(MIN_SCALE, min(MAX_SCALE, gene[4]))
            elif pos == 5:
                gene[5] += randint(-20, 20)
                gene[5] = gene[5] % 360
    
    
    def copy(self):
        return Individual(self.genom.copy())


class Genetics:

    def __init__(self, 
                 size_of_genom=DEFAULT_NUM_CHROMOSOMS, 
                 size_of_generation=DEFAULT_SIZE_OF_GENERATION,
                 survivor_rate=DEFAULT_SURVIVOR_RATE, 
                 mutation_rate=DEFAULT_MUTATION_RATE,
                 tournament_size=DEFAULT_TOURNAMENT_SIZE):
        self.size_of_genom = size_of_genom
        self.size_of_generation = size_of_generation
        self.survivor_rate = survivor_rate
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size
        self.winner = None


    def run(self, app):
        fitness_function = FitnessFunction(app).fitness_function
        population = self.create_random_population(self.size_of_generation)
        self.winner = population[0].genom
        print("=============================================================")
        print("starting genetic algorithm...")
        print("=============================================================")
        worst_survivor_fitness = -1000.0
        stagnation_count = 0
        generation = -1
        while True:
            generation += 1
            start_time = time()
            population.sort(key=lambda x: x.getFitness(fitness_function=fitness_function), reverse=True)
            self.winner = population[0].genom # store the best individuals genom
            num_survivors = int(self.size_of_generation * self.survivor_rate)
            survivors = population[:num_survivors]
            self.log_stats(population, generation, start_time, survivors)
            population = []
            if generation >= self.tournament_size:
                # final generation, do not breed further
                return
            if worst_survivor_fitness == survivors[-1].getFitness():
                stagnation_count += 1
                if stagnation_count >= 2:
                    print("Warn: Stagnation detected, countermeasures activated")
                    population = self.alternative_breed(fitness_function, survivors[0].getFitness(), generation)
                if (stagnation_count >= 3):
                    self.mutation_rate = self.mutation_rate * 1.05
            else:
                worst_survivor_fitness = survivors[-1].getFitness()
                stagnation_count = 0
            # Breeding
            while len(population) + len(survivors) < self.size_of_generation:
                child = Individual.breed(sample(survivors, NUM_PARENTS))
                population.append(child)
            # Mutation
            for m in range(int(len(population) * self.mutation_rate)):
                individual = population[randint(0,  len(population) - 1)]
                individual.mutate()
            # Elitism: carry over the best individuals
            population += survivors


    def alternative_breed(self, fitness_function, target_fitness, generation):
        # additional breeding to reach target fitness
        population = self.create_random_population(self.size_of_generation)
        last_worst_fitness = -1000.0
        while True:
            generation += 1
            start_time = time()
            population.sort(key=lambda x: x.getFitness(fitness_function=fitness_function), reverse=True)
            num_survivors = int(self.size_of_generation * self.survivor_rate)
            survivors = population[:num_survivors]
            self.log_stats(population, generation, start_time, survivors)
            winner = survivors[0]
            worst_survivor = survivors[-1]
            population = []  
            if (generation >= self.tournament_size) or (winner.getFitness() >= target_fitness) or (last_worst_fitness == worst_survivor.getFitness()):
                # do not breed further
                print("Info: Ending alternative breeding phase.")
                return survivors
            last_worst_fitness = survivors[-1].getFitness()
            # Breeding
            while len(population) + len(survivors) < self.size_of_generation:
                child = Individual.breed(sample(survivors, NUM_PARENTS))
                population.append(child)
            # Mutation
            for m in range(int(len(population) * self.mutation_rate)):
                individual = population[randint(0,  len(population) - 1)]
                individual.mutate()
            # Elitism: carry over the best individuals
            population += survivors


    def log_stats(self, population, generation, start_time, survivors):
        if generation % 25 == 0:
            print( "=============================================================")
            print("           best     worst   average   average")
            print("    #  survivor  survivor survivors       all  duration")
            #      ----+----|----+----|----+----|----+----|----+----|----+----|
        print(f"{generation:5d}"+
                  f"{survivors[0].getFitness():10.5f}"+
                  f"{survivors[-1].getFitness():10.5f}"+
                  f"{sum(ind.getFitness() for ind in survivors) / len(survivors):10.5f}"+
                  f"{sum(ind.getFitness() for ind in population) / len(population):10.5f}"+
                  f"{time() - start_time:10.3f}")


    def create_random_population(self, count):
        population = []
        for _ in range(count):
            population.append(Individual.random_individual(self.size_of_genom))
        return population


def _get_from_env(var_name, default, cast_type):
    value = os.getenv(var_name)
    if value is None:
        print(f"Info: Using {var_name}={default} (default)")
    else:
        try:
            value = cast_type(value)
            print(f"Info: Using {var_name}={value} (.env / environment)")
            return value
        except ValueError:
            print(f"Warning: Could not cast environment variable {var_name}='{value}' to {cast_type}. Using default {default}.")
    return default


if __name__ == "__main__":
    start_time = time()
    print("=============================================================")
    print("Info: Starting genetic algorithm... (cancel with Ctrl-C)")
    print("=============================================================")
    load_dotenv()
    SIZE_OF_GENOM = _get_from_env("SIZE_OF_GENOM", 100, int)
    SIZE_OF_GENERATION = _get_from_env("SIZE_OF_GENERATION", 50, int)
    SURVIVOR_RATE = _get_from_env("SURVIVOR_RATE", 0.3, float)
    MUTATION_RATE = _get_from_env("MUTATION_RATE", 0.1, float)
    TOURNAMENT_SIZE = _get_from_env("TOURNAMENT_SIZE", 100, int)
    print("=============================================================")
    genetics = Genetics(
        size_of_genom=SIZE_OF_GENOM,
        size_of_generation=SIZE_OF_GENERATION,
        survivor_rate=SURVIVOR_RATE,
        mutation_rate=MUTATION_RATE,
        tournament_size=TOURNAMENT_SIZE
    )
    try:
        visualization.headless_app(callback=genetics.run, prc_file="headless_128x128.prc")
    except KeyboardInterrupt:
        print("Info: Interrupted by user.")
    json_str = json.dumps(genetics.winner, indent=4, check_circular=False)
    filename = "winner.%d.json" % int(time())
    with open(filename, "w") as f:
        f.write(json_str)
    print("=============================================================")
    print(f"Info: SIZE_OF_GENOM        {SIZE_OF_GENOM}")
    print(f"Info: SIZE_OF_GENERATION   {SIZE_OF_GENERATION}")
    print(f"Info: SURVIVOR_RATE        {SURVIVOR_RATE}")
    print(f"Info: MUTATION_RATE        {MUTATION_RATE}")
    print(f"Info: TOURNAMENT_SIZE      {TOURNAMENT_SIZE}")
    print("=============================================================")
    print(f"Info: Total time elapsed   {time() - start_time:.3f} seconds")
    print(f"Info: Winner configuration saved to {filename}")
    print("=============================================================")
